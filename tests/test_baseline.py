"""Tests for baseline feature (load/generate/filter/auto-regen)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pydocfix.baseline import (
    compute_updated_baseline,
    filter_baseline_violations,
    generate_baseline,
    load_baseline,
    normalize_path,
)
from pydocfix.checker import check_file
from pydocfix.rules import build_registry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry():
    return build_registry(ignore=[], select=[], config=None)


def _run(source: str, path: Path | None = None) -> list:
    registry = _make_registry()
    fp = path or Path("test_module.py")
    diagnostics, _, _ = check_file(source, fp, registry.kind_map)
    return diagnostics


# ---------------------------------------------------------------------------
# load_baseline
# ---------------------------------------------------------------------------


class TestLoadBaseline:
    def test_returns_empty_when_file_missing(self, tmp_path):
        result = load_baseline(tmp_path / "nonexistent.json")
        assert result == {}

    def test_loads_valid_json(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        data = {
            "src/module.py": [
                {"symbol": "MyClass.method", "code": "PRM001"},
            ]
        }
        baseline_file.write_text(json.dumps(data), encoding="utf-8")

        result = load_baseline(baseline_file)
        assert result == data

    def test_returns_empty_on_invalid_json(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text("not valid json", encoding="utf-8")

        result = load_baseline(baseline_file)
        assert result == {}

    def test_returns_empty_when_root_is_list(self, tmp_path):
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

        result = load_baseline(baseline_file)
        assert result == {}


# ---------------------------------------------------------------------------
# generate_baseline
# ---------------------------------------------------------------------------


class TestGenerateBaseline:
    def test_writes_json_file(self, tmp_path):
        source = '''\
def greet(name: str) -> str:
    """Say hello.

    Returns:
        str: Greeting.
    """
    return f"Hello {name}"
'''
        fp = tmp_path / "mod.py"
        fp.write_text(source, encoding="utf-8")
        diagnostics = _run(source, fp)

        baseline_file = tmp_path / "baseline.json"
        generate_baseline({str(fp): diagnostics}, baseline_file)

        assert baseline_file.exists()
        data = json.loads(baseline_file.read_text(encoding="utf-8"))
        assert str(fp) in data

    def test_entries_have_symbol_and_code(self, tmp_path):
        source = '''\
def greet(name: str) -> str:
    """Say hello.

    Returns:
        str: Greeting.
    """
    return f"Hello {name}"
'''
        fp = tmp_path / "mod.py"
        fp.write_text(source, encoding="utf-8")
        diagnostics = _run(source, fp)

        assert diagnostics, "expected at least one diagnostic"
        assert all(d.symbol for d in diagnostics), "all diagnostics should have a symbol"

        baseline_file = tmp_path / "baseline.json"
        generate_baseline({str(fp): diagnostics}, baseline_file)

        data = json.loads(baseline_file.read_text(encoding="utf-8"))
        entries = data[str(fp)]
        for entry in entries:
            assert "symbol" in entry
            assert "code" in entry

    def test_creates_parent_directory(self, tmp_path):
        source = '''\
def f(x: int) -> int:
    """Short.

    Returns:
        int: Result.
    """
    return x
'''
        fp = tmp_path / "mod.py"
        fp.write_text(source, encoding="utf-8")
        diagnostics = _run(source, fp)

        nested = tmp_path / "subdir" / "baseline.json"
        generate_baseline({str(fp): diagnostics}, nested)
        assert nested.exists()

    def test_skips_diagnostics_without_symbol(self, tmp_path):
        """Module-level docstrings (empty symbol) should not appear in baseline."""
        baseline_file = tmp_path / "baseline.json"

        from pydocfix.rules._base import Diagnostic, Offset, Range

        d = Diagnostic(
            rule="SUM001",
            message="test",
            filepath="mod.py",
            range=Range(Offset(1, 0), Offset(1, 10)),
            symbol="",
        )
        generate_baseline({"mod.py": [d]}, baseline_file)

        data = json.loads(baseline_file.read_text(encoding="utf-8"))
        assert "mod.py" not in data  # skipped because symbol is empty


# ---------------------------------------------------------------------------
# Symbol computation via check_file
# ---------------------------------------------------------------------------


class TestSymbolComputation:
    def test_top_level_function_symbol(self, tmp_path):
        source = '''\
def greet(name: str) -> str:
    """Say hello.

    Returns:
        str: Greeting.
    """
    return f"Hello {name}"
'''
        diagnostics = _run(source, tmp_path / "m.py")
        assert diagnostics
        assert all(d.symbol == "greet" for d in diagnostics)

    def test_method_symbol_includes_class(self, tmp_path):
        source = '''\
class Greeter:
    def greet(self, name: str) -> str:
        """Say hello.

        Returns:
            str: Greeting.
        """
        return f"Hello {name}"
'''
        diagnostics = _run(source, tmp_path / "m.py")
        assert diagnostics
        assert all(d.symbol == "Greeter.greet" for d in diagnostics)

    def test_module_level_docstring_has_empty_symbol(self, tmp_path):
        source = '"""Module docstring."""\n'
        diagnostics = _run(source, tmp_path / "m.py")
        for d in diagnostics:
            assert d.symbol == ""


# ---------------------------------------------------------------------------
# filter_baseline_violations
# ---------------------------------------------------------------------------


class TestFilterBaselineViolations:
    def _make_diagnostic(self, symbol: str, code: str, filepath: str = "mod.py"):
        from pydocfix.rules._base import Diagnostic, Offset, Range

        return Diagnostic(
            rule=code,
            message="test",
            filepath=filepath,
            range=Range(Offset(1, 0), Offset(1, 10)),
            symbol=symbol,
        )

    def test_empty_baseline_returns_all(self):
        d = self._make_diagnostic("my_func", "PRM001")
        result = filter_baseline_violations([d], {}, "mod.py")
        assert result == [d]

    def test_matching_entry_is_removed(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        d = self._make_diagnostic("my_func", "PRM001")
        result = filter_baseline_violations([d], baseline, "mod.py")
        assert result == []

    def test_non_matching_entry_is_kept(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        d = self._make_diagnostic("another_func", "PRM001")
        result = filter_baseline_violations([d], baseline, "mod.py")
        assert result == [d]

    def test_different_code_is_kept(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        d = self._make_diagnostic("my_func", "RTN001")
        result = filter_baseline_violations([d], baseline, "mod.py")
        assert result == [d]

    def test_different_file_is_kept(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        d = self._make_diagnostic("my_func", "PRM001", filepath="other.py")
        result = filter_baseline_violations([d], baseline, "other.py")
        assert result == [d]

    def test_partial_filter(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        d1 = self._make_diagnostic("my_func", "PRM001")
        d2 = self._make_diagnostic("my_func", "RTN001")
        result = filter_baseline_violations([d1, d2], baseline, "mod.py")
        assert result == [d2]


# ---------------------------------------------------------------------------
# compute_updated_baseline
# ---------------------------------------------------------------------------


class TestComputeUpdatedBaseline:
    def _make_diagnostic(self, symbol: str, code: str, filepath: str = "mod.py"):
        from pydocfix.rules._base import Diagnostic, Offset, Range

        return Diagnostic(
            rule=code,
            message="test",
            filepath=filepath,
            range=Range(Offset(1, 0), Offset(1, 10)),
            symbol=symbol,
        )

    def test_no_change_when_all_violations_remain(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        actual = {"mod.py": [self._make_diagnostic("my_func", "PRM001")]}
        changed, updated = compute_updated_baseline(baseline, actual)
        assert not changed
        assert updated == baseline

    def test_changed_when_violation_is_fixed(self):
        baseline = {"mod.py": [{"symbol": "my_func", "code": "PRM001"}]}
        # No violations remain in mod.py
        actual: dict = {}
        changed, updated = compute_updated_baseline(baseline, actual)
        assert changed
        assert "mod.py" not in updated

    def test_unfixed_violations_remain_in_updated(self):
        baseline = {
            "mod.py": [
                {"symbol": "func_a", "code": "PRM001"},
                {"symbol": "func_b", "code": "RTN001"},
            ]
        }
        # Only func_a violation remains
        actual = {"mod.py": [self._make_diagnostic("func_a", "PRM001")]}
        changed, updated = compute_updated_baseline(baseline, actual)
        assert changed
        assert updated["mod.py"] == [{"symbol": "func_a", "code": "PRM001"}]


# ---------------------------------------------------------------------------
# Integration: baseline suppresses violations in check_file
# ---------------------------------------------------------------------------


class TestBaselineIntegration:
    def test_baseline_suppresses_known_violation(self, tmp_path):
        source = '''\
def greet(name: str) -> str:
    """Say hello.

    Returns:
        str: Greeting.
    """
    return f"Hello {name}"
'''
        fp = tmp_path / "mod.py"
        fp.write_text(source, encoding="utf-8")

        # Get actual violations
        violations = _run(source, fp)
        assert violations, "need at least one violation to test suppression"

        # Generate baseline from violations
        baseline = {str(fp): violations}
        baseline_file = tmp_path / "baseline.json"
        generate_baseline(baseline, baseline_file)

        # Load and filter
        loaded = load_baseline(baseline_file)
        filtered = filter_baseline_violations(violations, loaded, str(fp))
        assert filtered == [], "all violations should be suppressed by baseline"

    def test_new_violations_not_suppressed(self, tmp_path):
        source = '''\
def greet(name: str) -> str:
    """Say hello.

    Returns:
        str: Greeting.
    """
    return f"Hello {name}"
'''
        fp = tmp_path / "mod.py"
        fp.write_text(source, encoding="utf-8")

        violations = _run(source, fp)
        # Baseline that only covers a different function
        baseline = {str(fp): [{"symbol": "other_func", "code": violations[0].rule}]}
        filtered = filter_baseline_violations(violations, baseline, str(fp))
        assert len(filtered) == len(violations), "none should be suppressed"


# ---------------------------------------------------------------------------
# normalize_path
# ---------------------------------------------------------------------------


class TestNormalizePath:
    def test_relative_posix_path_under_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        fp = root / "src" / "module.py"
        fp.parent.mkdir(parents=True)
        fp.touch()
        assert normalize_path(fp, root) == "src/module.py"

    def test_file_directly_under_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        fp = root / "module.py"
        fp.touch()
        assert normalize_path(fp, root) == "module.py"

    def test_fallback_when_not_under_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        outside = tmp_path / "other" / "module.py"
        outside.parent.mkdir(parents=True)
        outside.touch()
        result = normalize_path(outside, root)
        # Falls back to resolved absolute path — not a relative path
        assert result == str(outside.resolve())
        assert "project" not in result

    def test_resolves_symlinks(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        real = root / "src" / "module.py"
        real.parent.mkdir()
        real.touch()
        link = root / "link.py"
        link.symlink_to(real)
        # Both real and symlink should normalise to a path within the root
        result = normalize_path(link, root)
        assert result == "src/module.py"

    def test_uses_forward_slashes(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        fp = root / "a" / "b" / "c.py"
        fp.parent.mkdir(parents=True)
        fp.touch()
        assert "/" in normalize_path(fp, root)
        assert "\\" not in normalize_path(fp, root)
