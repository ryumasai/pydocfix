#!/usr/bin/env python3
"""Benchmark pydocfix against pydocstyle, pydoclint, and ruff (D rules).

Usage:
    python benchmarks/bench.py [--target httpx|requests|flask|rich]
    python benchmarks/bench.py --target /path/to/local/project
"""

from __future__ import annotations

import argparse
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
        elif tool == "pydocstyle":
            r = subprocess.run(["pydocstyle", "--version"], capture_output=True, text=True)
            return r.stdout.strip()
        elif tool == "pydoclint":
            r = subprocess.run(["pydoclint", "--version"], capture_output=True, text=True)
            return r.stdout.strip()
        elif tool == "ruff":
            r = subprocess.run(["ruff", "version"], capture_output=True, text=True)
            return f"ruff {r.stdout.strip()}"
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
        try:
            lines += len(p.read_text(errors="replace").splitlines())
        except OSError:
            pass
    return files, lines


def find_python_src(target: Path) -> Path:
    """Find the best source directory within a project."""
    src = target / "src"
    if src.is_dir():
        return src
    for candidate in sorted(target.iterdir()):
        if candidate.is_dir() and (candidate / "__init__.py").exists():
            return candidate
    return target


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
    cmd = ["pydocfix", "check", "--select", "ALL", str(target)]
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


def run_pydocstyle(target: Path, runs: int) -> BenchResult:
    result = BenchResult(tool="pydocstyle", version=get_version("pydocstyle"), has_autofix=False)
    cmd = ["pydocstyle", "--count", str(target)]
    result.elapsed_secs, r = _timed_runs(cmd, runs)
    result.exit_code = r.returncode

    codes: set[str] = set()
    count = 0
    for line in (r.stdout + r.stderr).splitlines():
        for token in line.split():
            if token.startswith("D") and len(token) >= 4 and token[:4].replace("D", "").isdigit():
                codes.add(token.rstrip(":"))
                count += 1
                break
    result.violation_count = count
    result.rule_codes = codes
    return result


def run_pydoclint(target: Path, runs: int) -> BenchResult:
    result = BenchResult(tool="pydoclint", version=get_version("pydoclint"), has_autofix=False)
    cmd = ["pydoclint", "--style=google", "--quiet", str(target)]
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


def run_ruff(target: Path, runs: int) -> BenchResult:
    result = BenchResult(tool="ruff", version=get_version("ruff"), has_autofix=True)
    cmd = [
        "ruff",
        "check",
        "--select",
        "D",
        "--output-format",
        "json",
        "--no-cache",
        str(target),
    ]
    result.elapsed_secs, r = _timed_runs(cmd, runs)
    result.exit_code = r.returncode

    codes: set[str] = set()
    count = 0
    try:
        violations = json.loads(r.stdout)
        for v in violations:
            codes.add(v.get("code", ""))
            count += 1
    except (json.JSONDecodeError, TypeError):
        for line in r.stdout.splitlines():
            count += 1
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


def print_results(results: list[BenchResult], target: Path, bench_runs: int) -> None:
    py_files, py_lines = count_python_files(target)

    print()
    print("=" * 80)
    print("  Benchmark: pydocfix vs other docstring linters")
    print(f"  Target: {target.name}")
    print(f"  Python files: {py_files:,}  |  Lines: {py_lines:,}")
    print(f"  Runs: {bench_runs} (+ {WARMUP_RUNS} warmup)")
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
        elif tool in ("pydocstyle", "ruff"):
            return "Style/Formatting"
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
    print(f"{'Feature':<35} {'pydocfix':>12} {'pydocstyle':>12} {'pydoclint':>12} {'ruff':>12}")
    print("-" * 85)

    features = {
        "Auto-fix (safe)": ("Yes", "No", "No", "Partial"),
        "Auto-fix (unsafe)": ("Yes", "No", "No", "No"),
        "Google style": ("Yes", "Yes", "Yes", "Yes"),
        "NumPy style": ("Yes", "Yes", "Yes", "Yes"),
        "Param type checking": ("Yes", "No", "Yes", "No"),
        "Return type checking": ("Yes", "No", "Yes", "No"),
        "Yield checking": ("Yes", "No", "Yes", "No"),
        "Raises checking": ("Yes", "No", "Yes", "No"),
        "Default value checking": ("Yes", "No", "No", "No"),
        "Iterative fix loop": ("Yes", "No", "No", "No"),
    }
    for feat, (a, b, c, d) in features.items():
        print(f"{feat:<35} {a:>12} {b:>12} {c:>12} {d:>12}")
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
        default="httpx",
        help="OSS project name (httpx, requests, flask, rich) or path to local project",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_BENCH_RUNS,
        help=f"Number of benchmark runs (default: {DEFAULT_BENCH_RUNS})",
    )
    args = parser.parse_args()
    bench_runs: int = args.runs

    target_path = Path(args.target)
    tmp_dir: Path | None = None

    if target_path.is_dir():
        scan_path = find_python_src(target_path)
    elif args.target in OSS_REPOS:
        tmp = tempfile.mkdtemp(prefix="pydocfix_bench_")
        tmp_dir = Path(tmp)
        repo_path = clone_repo(args.target, tmp_dir)
        scan_path = find_python_src(repo_path)
    else:
        print(f"Unknown target: {args.target}", file=sys.stderr)
        print(
            f"Available: {', '.join(OSS_REPOS.keys())} or a local path",
            file=sys.stderr,
        )
        sys.exit(1)

    py_files, py_lines = count_python_files(scan_path)
    print(f"Target: {args.target} ({scan_path})")
    print(f"Python files: {py_files:,} | Lines: {py_lines:,}")
    print()

    try:
        results: list[BenchResult] = []

        for name, runner in [
            ("pydocfix", run_pydocfix),
            ("pydocstyle", run_pydocstyle),
            ("pydoclint", run_pydoclint),
            ("ruff", run_ruff),
        ]:
            print(f"Running {name} ...")
            results.append(runner(scan_path, bench_runs))

        print_results(results, scan_path, bench_runs)

    finally:
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
