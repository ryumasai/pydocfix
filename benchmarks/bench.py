#!/usr/bin/env python3
"""Benchmark pydocfix against pydoclint.

Usage:
    python benchmarks/bench.py [--target httpx|numpy] [--docstyle google|numpy]
    python benchmarks/bench.py --target /path/to/local/project --docstyle google

pydoclint is configured to match pydocfix's rule scope:
  --style <google|numpy>                 docstring style to parse
  --arg-type-hints-in-signature False    pydocfix PRM103-106 disabled by default
  --arg-type-hints-in-docstring False    (type_annotation_style not set → omitted)"""

from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

# --- OSS repos to benchmark against ---
OSS_REPOS: dict[str, str] = {
    "httpx": "https://github.com/encode/httpx.git",
    "requests": "https://github.com/psf/requests.git",
    "flask": "https://github.com/pallets/flask.git",
    "rich": "https://github.com/Textualize/rich.git",
    "numpy": "https://github.com/numpy/numpy.git",
    "scipy": "https://github.com/scipy/scipy.git",
    "pandas": "https://github.com/pandas-dev/pandas.git",
    "scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
}

# Repos that primarily use each docstring style
STYLE_DEFAULT_TARGET: dict[str, str] = {
    "google": "httpx",
    "numpy": "numpy",
}

# pydoclint options that align its checks to pydocfix's rule scope:
#   --arg-type-hints-in-signature False   pydocfix disables PRM103-106 by default
#   --arg-type-hints-in-docstring False   (type_annotation_style not set → omitted)
#   --style <style>                       explicit style; pydocfix auto-detects
PYDOCLINT_ALIGN_OPTS: list[str] = [
    "--arg-type-hints-in-signature",
    "False",
    "--arg-type-hints-in-docstring",
    "False",
]

WARMUP_RUNS = 1
DEFAULT_BENCH_RUNS = 5


@dataclass
class BenchResult:
    tool: str
    version: str
    elapsed_secs: list[float] = field(default_factory=list)
    stddev_secs: float = 0.0
    min_secs: float = 0.0
    max_secs: float = 0.0
    violation_count: int = 0
    rule_codes: set[str] = field(default_factory=set)
    has_autofix: bool = False
    exit_code: int = 0
    error: str = ""


def get_version(tool: str) -> str:
    """Get tool version string."""
    try:
        if tool == "pydocfix":
            r = subprocess.run(["pydocfix", "--version"], capture_output=True, text=True)
            return r.stdout.strip()
        elif tool == "pydoclint":
            r = subprocess.run(["pydoclint", "--version"], capture_output=True, text=True)
            return r.stdout.strip()
    except FileNotFoundError:
        return "not found"
    return "unknown"


def count_python_files(target: Path) -> tuple[int, int]:
    """Count .py files and total lines."""
    files = 0
    lines = 0
    skip = {".git", "__pycache__", ".tox", ".venv", "venv", "node_modules"}
    for p in target.rglob("*.py"):
        if any(part in skip for part in p.parts):
            continue
        files += 1
        with contextlib.suppress(OSError):
            lines += len(p.read_text(errors="replace").splitlines())
    return files, lines


def find_python_src(target: Path) -> Path:
    """Find the best source directory within a project."""
    src = target / "src"
    if src.is_dir():
        return src
    # Pick the candidate with the most .py files to avoid landing in a small
    # auxiliary directory (e.g. benchmarks/) instead of the main package.
    best: Path | None = None
    best_count = -1
    for candidate in target.iterdir():
        if not candidate.is_dir() or not (candidate / "__init__.py").exists():
            continue
        count = sum(1 for _ in candidate.rglob("*.py"))
        if count > best_count:
            best_count = count
            best = candidate
    return best if best is not None else target


def _timed_runs(cmd: list[str], runs: int) -> tuple[list[float], float, float, float, subprocess.CompletedProcess[str]]:
    """Run via hyperfine (warmup + timed runs).

    Returns (all_times_secs, stddev, min, max, last_subprocess_result).
    Falls back to manual timing if hyperfine is unavailable.
    """
    if shutil.which("hyperfine"):
        return _timed_runs_hyperfine(cmd, runs)
    return _timed_runs_manual(cmd, runs)


def _timed_runs_hyperfine(
    cmd: list[str], runs: int
) -> tuple[list[float], float, float, float, subprocess.CompletedProcess[str]]:
    """Time a command using hyperfine with JSON export."""
    import tempfile as _tf

    with _tf.NamedTemporaryFile(suffix=".json", delete=False) as f:
        json_path = Path(f.name)

    hyperfine_cmd = [
        "hyperfine",
        "--warmup",
        str(WARMUP_RUNS),
        "--runs",
        str(runs),
        "--export-json",
        str(json_path),
        "--style",
        "none",  # no ANSI/progress bars
        "--ignore-failure",  # tools may exit 1 when violations are found
        " ".join(cmd),
    ]
    subprocess.run(hyperfine_cmd, capture_output=True)

    data = json.loads(json_path.read_text())
    json_path.unlink(missing_ok=True)

    result_data = data["results"][0]
    times: list[float] = result_data["times"]
    stddev: float = result_data.get("stddev", 0.0)
    min_t: float = result_data.get("min", min(times))
    max_t: float = result_data.get("max", max(times))

    # Run once more to capture output for violation parsing
    last = subprocess.run(cmd, capture_output=True, text=True)
    return times, stddev, min_t, max_t, last


def _timed_runs_manual(
    cmd: list[str], runs: int
) -> tuple[list[float], float, float, float, subprocess.CompletedProcess[str]]:
    """Fallback: manual warmup + timing loop."""
    import statistics

    for _ in range(WARMUP_RUNS):
        subprocess.run(cmd, capture_output=True, text=True)

    elapsed: list[float] = []
    r = None
    for _ in range(runs):
        t0 = time.perf_counter()
        r = subprocess.run(cmd, capture_output=True, text=True)
        elapsed.append(time.perf_counter() - t0)
    assert r is not None
    stddev = statistics.stdev(elapsed) if len(elapsed) > 1 else 0.0
    return elapsed, stddev, min(elapsed), max(elapsed), r


# --- Tool runners ---


def run_pydocfix(target: Path, runs: int, jobs: int | None = None) -> BenchResult:
    result = BenchResult(tool="pydocfix", version=get_version("pydocfix"), has_autofix=True)
    cmd = ["pydocfix", "check", str(target)]
    if jobs is not None:
        cmd += ["--jobs", str(jobs)]
    result.elapsed_secs, result.stddev_secs, result.min_secs, result.max_secs, r = _timed_runs(cmd, runs)
    result.exit_code = r.returncode

    codes: set[str] = set()
    count = 0
    for line in r.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) >= 4:
            msg = parts[3].strip()
            code = msg.split()[0] if msg else ""
            if code and code.startswith(("CLS", "DOC", "SUM", "PRM", "RTN", "YLD", "RIS")):
                codes.add(code)
                count += 1
    result.violation_count = count
    result.rule_codes = codes
    return result


def run_pydoclint(target: Path, runs: int, docstyle: str = "numpy") -> BenchResult:
    result = BenchResult(tool="pydoclint", version=get_version("pydoclint"), has_autofix=False)
    cmd = [
        "pydoclint",
        "--quiet",
        f"--style={docstyle}",
        *PYDOCLINT_ALIGN_OPTS,
        str(target),
    ]
    result.elapsed_secs, result.stddev_secs, result.min_secs, result.max_secs, r = _timed_runs(cmd, runs)
    result.exit_code = r.returncode

    codes: set[str] = set()
    count = 0
    for line in (r.stdout + r.stderr).splitlines():
        for token in line.split():
            if token.startswith("DOC") and len(token) >= 6:
                code = token.rstrip(":").rstrip(",")
                if code[:6].replace("DOC", "").isdigit():
                    codes.add(code[:6])
                    count += 1
                    break
    result.violation_count = count
    result.rule_codes = codes
    return result


# --- Output formatting ---


def fmt_secs(secs: float) -> str:
    return f"{secs * 1000:.0f}ms" if secs < 1.0 else f"{secs:.2f}s"


def fmt_time(r: BenchResult) -> str:
    med = median_secs(r.elapsed_secs)
    s = fmt_secs(med)
    if r.stddev_secs > 0:
        s += f" ± {fmt_secs(r.stddev_secs)}"
    return s


def median_secs(secs: list[float]) -> float:
    if not secs:
        return 0.0
    return sorted(secs)[len(secs) // 2]


def print_results(
    results: list[BenchResult],
    target: Path,
    bench_runs: int,
    docstyle: str = "numpy",
) -> None:
    py_files, py_lines = count_python_files(target)

    pydoclint_opts = f"--style={docstyle} " + " ".join(PYDOCLINT_ALIGN_OPTS)

    print()
    print("=" * 80)
    print("  Benchmark: pydocfix vs pydoclint")
    print(f"  Target: {target.name}  |  Docstring style: {docstyle}")
    print(f"  Python files: {py_files:,}  |  Lines: {py_lines:,}")
    print(f"  Runs: {bench_runs} (+ {WARMUP_RUNS} warmup)")
    print(f"  pydoclint opts: {pydoclint_opts}")
    print("=" * 80)
    print()

    # Speed comparison table
    pydocfix_time = next(
        (median_secs(r.elapsed_secs) for r in results if r.tool == "pydocfix"),
        1.0,
    )

    print("## Execution Speed (median)")
    print()
    print(f"{'Tool':<20} {'Version':<25} {'Time (median ± σ)':>22} {'Relative':>10}")
    print("-" * 79)

    for r in sorted(results, key=lambda x: median_secs(x.elapsed_secs)):
        med = median_secs(r.elapsed_secs)
        rel = f"{med / pydocfix_time:.1f}x" if pydocfix_time > 0 else "N/A"
        print(f"{r.tool:<20} {r.version:<25} {fmt_time(r):>22} {rel:>10}")

    print()

    # Violation count comparison
    print("## Violations Detected")
    print()
    print(f"{'Tool':<20} {'Violations':>12} {'Unique Rules':>14} {'Auto-fix':>10}")
    print("-" * 58)
    for r in results:
        fix_str = "Yes" if r.has_autofix else "No"
        print(f"{r.tool:<20} {r.violation_count:>12,} {len(r.rule_codes):>14} {fix_str:>10}")

    print()

    # Detected rule codes per tool
    print("## Detected Rule Codes")
    print()
    for r in results:
        codes = sorted(r.rule_codes)
        print(f"  {r.tool}: {', '.join(codes) if codes else '(none)'}")
    print()


@dataclass
class TargetBenchResult:
    """Aggregated benchmark results for one target."""

    target_name: str
    scan_path: Path
    py_files: int
    py_lines: int
    parallel: BenchResult
    single: BenchResult
    pydoclint: BenchResult


def print_readme_section(
    targets: list[TargetBenchResult],
    bench_runs: int,
) -> None:
    """Print README-ready markdown tables (parallel + single-thread) to stdout."""

    def fmt(secs: float) -> str:
        return f"{secs:.2f} sec"

    def spdup(fix: float, ref: float) -> str:
        return f"**{ref / fix:.1f}x**"

    def speed_row(t: TargetBenchResult, secs: float, pdl: float) -> str:
        lines_k = f"{round(t.py_lines / 1000)}K"
        url = OSS_REPOS.get(t.target_name, "#").removesuffix(".git")
        return (
            f"| [{t.target_name}]({url}) | {t.py_files} | {lines_k} | {fmt(secs)} | {fmt(pdl)} | {spdup(secs, pdl)} |"
        )

    def violation_row(t: TargetBenchResult) -> str:
        url = OSS_REPOS.get(t.target_name, "#").removesuffix(".git")
        return f"| [{t.target_name}]({url}) | {t.parallel.violation_count:,} | {t.pydoclint.violation_count:,} |"

    print()
    print("=" * 80)
    print("  README Markdown (copy-paste ready)")
    print("=" * 80)
    print()
    print("#### Parallel (default, auto-detected cores \u2014 10-core machine)")
    print()
    print("| Project | Files | Lines | pydocfix | pydoclint | Speedup |")
    print("|---------|------:|------:|---------:|----------:|--------:|")
    for t in targets:
        print(speed_row(t, median_secs(t.parallel.elapsed_secs), median_secs(t.pydoclint.elapsed_secs)))
    print()
    print("#### Single-threaded (`--jobs 1`)")
    print()
    print("| Project | Files | Lines | pydocfix | pydoclint | Speedup |")
    print("|---------|------:|------:|---------:|----------:|--------:|")
    for t in targets:
        print(speed_row(t, median_secs(t.single.elapsed_secs), median_secs(t.pydoclint.elapsed_secs)))
    print()
    print(f"> Median of {bench_runs} runs (+ {WARMUP_RUNS} warmup). pydoclint runs single-threaded only.")
    print()
    print("#### Violations detected")
    print()
    print("| Project | pydocfix | pydoclint |")
    print("|---------|------:|------:|")
    for t in targets:
        print(violation_row(t))
    print()
    print("## Violations (detail)")
    for t in targets:
        print(
            f"  [{t.target_name}] pydocfix:  {t.parallel.violation_count:,} ({len(t.parallel.rule_codes)} unique rules)"
        )
        print(
            f"  [{t.target_name}] pydoclint: {t.pydoclint.violation_count:,} "
            f"({len(t.pydoclint.rule_codes)} unique rules)"
        )
    print()


def clone_repo(name: str, tmp_dir: Path) -> Path:
    url = OSS_REPOS[name]
    dest = tmp_dir / name
    print(f"Cloning {name} from {url} ...")
    subprocess.run(["git", "clone", "--depth=1", "--quiet", url, str(dest)], check=True)
    return dest


def _resolve_target(target_arg: str, tmp_dir: Path) -> tuple[Path, Path]:
    """Resolve a target name/path to (repo_path, scan_path). Clones if needed."""
    target_path = Path(target_arg)
    if target_path.is_dir():
        return target_path, find_python_src(target_path)
    if target_arg in OSS_REPOS:
        repo_path = clone_repo(target_arg, tmp_dir)
        return repo_path, find_python_src(repo_path)
    print(f"Unknown target: {target_arg}", file=sys.stderr)
    print(f"Available: {', '.join(OSS_REPOS.keys())} or a local path", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark pydocfix against other linters")
    parser.add_argument(
        "--target",
        default=None,
        help=(
            "Comma-separated OSS project names or local paths "
            "(e.g. numpy,scikit-learn). Defaults to the style's canonical target."
        ),
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_BENCH_RUNS,
        help=f"Number of benchmark runs (default: {DEFAULT_BENCH_RUNS})",
    )
    parser.add_argument(
        "--docstyle",
        choices=["google", "numpy"],
        default="numpy",
        help="Docstring style to benchmark (google or numpy). Affects pydoclint --style.",
    )
    args = parser.parse_args()
    bench_runs: int = args.runs
    docstyle: str = args.docstyle

    raw_targets = args.target or STYLE_DEFAULT_TARGET[docstyle]
    target_args = [t.strip() for t in raw_targets.split(",") if t.strip()]

    tmp_dir = Path(tempfile.mkdtemp(prefix="pydocfix_bench_"))
    all_target_results: list[TargetBenchResult] = []

    try:
        for target_arg in target_args:
            _, scan_path = _resolve_target(target_arg, tmp_dir)
            py_files, py_lines = count_python_files(scan_path)
            print(f"Target: {target_arg} ({scan_path})")
            print(f"Docstyle: {docstyle}")
            print(f"Python files: {py_files:,} | Lines: {py_lines:,}")
            print()

            results: list[BenchResult] = []

            print(f"[{target_arg}] Running pydocfix (parallel) ...")
            parallel_fix = run_pydocfix(scan_path, bench_runs)
            results.append(parallel_fix)

            print(f"[{target_arg}] Running pydocfix (--jobs 1) ...")
            single_fix = run_pydocfix(scan_path, bench_runs, jobs=1)

            print(f"[{target_arg}] Running pydoclint ...")
            pydoclint_res = run_pydoclint(scan_path, bench_runs, docstyle=docstyle)
            results.append(pydoclint_res)

            print_results(results, scan_path, bench_runs, docstyle=docstyle)

            all_target_results.append(
                TargetBenchResult(
                    target_name=target_arg,
                    scan_path=scan_path,
                    py_files=py_files,
                    py_lines=py_lines,
                    parallel=parallel_fix,
                    single=single_fix,
                    pydoclint=pydoclint_res,
                )
            )

        print_readme_section(all_target_results, bench_runs)

    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
