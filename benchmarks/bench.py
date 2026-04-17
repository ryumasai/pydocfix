#!/usr/bin/env python3
"""Benchmark pydocfix against pydoclint.

Usage:
    python benchmarks/bench.py [--target httpx|numpy] [--docstyle google|numpy]
    python benchmarks/bench.py --target /path/to/local/project --docstyle google

pydoclint is configured to match pydocfix's rule scope:
  --style <google|numpy>         docstring style to parse
  --check-class-attributes False pydocfix has no class-attribute rules"""

from __future__ import annotations

import argparse
import contextlib
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
#   --check-class-attributes False  pydocfix has no class-attribute rules
#   --style <style>                 explicit style; pydocfix auto-detects
PYDOCLINT_ALIGN_OPTS: list[str] = ["--check-class-attributes", "False"]

WARMUP_RUNS = 1
DEFAULT_BENCH_RUNS = 5


@dataclass
class BenchResult:
    tool: str
    version: str
    elapsed_secs: list[float] = field(default_factory=list)
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


def _timed_runs(cmd: list[str], runs: int) -> tuple[list[float], subprocess.CompletedProcess[str]]:
    """Run warmup + timed runs, return (elapsed list, last CompletedProcess)."""
    for _ in range(WARMUP_RUNS):
        subprocess.run(cmd, capture_output=True, text=True)

    elapsed: list[float] = []
    r = None
    for _ in range(runs):
        t0 = time.perf_counter()
        r = subprocess.run(cmd, capture_output=True, text=True)
        t1 = time.perf_counter()
        elapsed.append(t1 - t0)
    assert r is not None
    return elapsed, r


# --- Tool runners ---


def run_pydocfix(target: Path, runs: int) -> BenchResult:
    result = BenchResult(tool="pydocfix", version=get_version("pydocfix"), has_autofix=True)
    cmd = ["pydocfix", "check", str(target)]
    result.elapsed_secs, r = _timed_runs(cmd, runs)
    result.exit_code = r.returncode

    codes: set[str] = set()
    count = 0
    for line in r.stdout.splitlines():
        parts = line.split(":", 3)
        if len(parts) >= 4:
            msg = parts[3].strip()
            code = msg.split()[0] if msg else ""
            if code and code.startswith(("DOC", "SUM", "PRM", "RTN", "YLD", "RIS")):
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
    result.elapsed_secs, r = _timed_runs(cmd, runs)
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


def fmt_time(secs: list[float]) -> str:
    if not secs:
        return "N/A"
    median = sorted(secs)[len(secs) // 2]
    return f"{median * 1000:.0f}ms" if median < 1.0 else f"{median:.2f}s"


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
    print(f"{'Tool':<20} {'Version':<25} {'Time':>10} {'Relative':>10}")
    print("-" * 67)

    for r in sorted(results, key=lambda x: median_secs(x.elapsed_secs)):
        med = median_secs(r.elapsed_secs)
        rel = f"{med / pydocfix_time:.1f}x" if pydocfix_time > 0 else "N/A"
        print(f"{r.tool:<20} {r.version:<25} {fmt_time(r.elapsed_secs):>10} {rel:>10}")

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

    # Rule categories
    print("## Rule Categories Covered")
    print()

    def categorize(tool: str, code: str) -> str:
        if tool == "pydocfix":
            for prefix, cat in [
                ("SUM", "Summary"),
                ("DOC", "Docstring"),
                ("PRM", "Parameters"),
                ("RTN", "Returns"),
                ("YLD", "Yields"),
                ("RIS", "Raises"),
            ]:
                if code.startswith(prefix):
                    return cat
        elif tool == "pydoclint":
            for prefix, cat in [
                ("DOC0", "Docstring"),
                ("DOC1", "Parameters"),
                ("DOC2", "Returns"),
                ("DOC3", "Class"),
                ("DOC4", "Yields"),
                ("DOC5", "Raises"),
                ("DOC6", "Attributes"),
            ]:
                if code.startswith(prefix):
                    return cat
        return "Other"

    tools = [r.tool for r in results]
    all_cats: set[str] = set()
    tool_cat_codes: dict[str, dict[str, set[str]]] = {r.tool: {} for r in results}
    for r in results:
        for code in r.rule_codes:
            cat = categorize(r.tool, code)
            all_cats.add(cat)
            tool_cat_codes[r.tool].setdefault(cat, set()).add(code)

    header = f"{'Category':<20}" + "".join(f"{t:>14}" for t in tools)
    print(header)
    print("-" * (20 + 14 * len(tools)))
    for cat in sorted(all_cats):
        row = f"{cat:<20}"
        for t in tools:
            n = len(tool_cat_codes[t].get(cat, set()))
            row += f"{n:>14}"
        print(row)

    print()

    # Detected rule codes per tool
    print("## Detected Rule Codes")
    print()
    for r in results:
        codes = sorted(r.rule_codes)
        print(f"  {r.tool}: {', '.join(codes) if codes else '(none)'}")
    print()

    # Feature comparison
    print("## Feature Comparison")
    print()
    print(f"{'Feature':<35} {'pydocfix':>12} {'pydoclint':>12}")
    print("-" * 61)

    features = {
        "Auto-fix (safe)": ("Yes", "No"),
        "Auto-fix (unsafe)": ("Yes", "No"),
        "Google style": ("Yes", "Yes"),
        "NumPy style": ("Yes", "Yes"),
        "Param type checking": ("Yes", "Yes"),
        "Return type checking": ("Yes", "Yes"),
        "Yield checking": ("Yes", "Yes"),
        "Raises checking": ("Yes", "Yes"),
        "Default value checking": ("Yes", "No"),
        "Iterative fix loop": ("Yes", "No"),
    }
    for feat, (a, b) in features.items():
        print(f"{feat:<35} {a:>12} {b:>12}")
    print()


def clone_repo(name: str, tmp_dir: Path) -> Path:
    url = OSS_REPOS[name]
    dest = tmp_dir / name
    print(f"Cloning {name} from {url} ...")
    subprocess.run(["git", "clone", "--depth=1", "--quiet", url, str(dest)], check=True)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark pydocfix against other linters")
    parser.add_argument(
        "--target",
        default=None,
        help="OSS project name or path to local project (default depends on --docstyle)",
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

    target_arg: str = args.target or STYLE_DEFAULT_TARGET[docstyle]

    target_path = Path(target_arg)
    tmp_dir: Path | None = None

    if target_path.is_dir():
        scan_path = find_python_src(target_path)
    elif target_arg in OSS_REPOS:
        tmp = tempfile.mkdtemp(prefix="pydocfix_bench_")
        tmp_dir = Path(tmp)
        repo_path = clone_repo(target_arg, tmp_dir)
        scan_path = find_python_src(repo_path)
    else:
        print(f"Unknown target: {target_arg}", file=sys.stderr)
        print(
            f"Available: {', '.join(OSS_REPOS.keys())} or a local path",
            file=sys.stderr,
        )
        sys.exit(1)

    py_files, py_lines = count_python_files(scan_path)
    print(f"Target: {target_arg} ({scan_path})")
    print(f"Docstyle: {docstyle}")
    print(f"Python files: {py_files:,} | Lines: {py_lines:,}")
    print()

    try:
        results: list[BenchResult] = []

        print("Running pydocfix ...")
        results.append(run_pydocfix(scan_path, bench_runs))

        print("Running pydoclint ...")
        results.append(run_pydoclint(scan_path, bench_runs, docstyle=docstyle))

        print_results(results, scan_path, bench_runs, docstyle=docstyle)

    finally:
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
