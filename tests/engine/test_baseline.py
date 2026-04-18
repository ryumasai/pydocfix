"""Tests for baseline module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from pydocfix.baseline import (
    compute_updated_baseline,
    filter_baseline_violations,
    generate_baseline,
    load_baseline,
    normalize_path,
    write_baseline,
)


def _make_diagnostic(code: str, symbol: str):
    """Create a mock diagnostic."""
    d = MagicMock()
    d.rule = code
    d.symbol = symbol
    return d


class TestNormalizePath:
    """Tests for normalize_path()."""

    def test_relative_path(self, tmp_path):
        """Returns relative POSIX path."""
        file = tmp_path / "src" / "module.py"
        file.parent.mkdir(parents=True)
        file.touch()

        result = normalize_path(file, tmp_path)

        assert result == "src/module.py"

    def test_file_at_root(self, tmp_path):
        """File at root returns just filename."""
        file = tmp_path / "module.py"
        file.touch()

        result = normalize_path(file, tmp_path)

        assert result == "module.py"


class TestLoadBaseline:
    """Tests for load_baseline()."""

    def test_loads_existing(self, tmp_path):
        """Loads existing baseline file."""
        baseline_file = tmp_path / "baseline.json"
        data = {"src/module.py": [{"symbol": "foo", "code": "SUM001"}]}
        baseline_file.write_text(json.dumps(data))

        result = load_baseline(baseline_file)

        assert "src/module.py" in result
        assert result["src/module.py"][0]["code"] == "SUM001"

    def test_missing_file_returns_empty(self, tmp_path):
        """Missing baseline file returns empty dict."""
        result = load_baseline(tmp_path / "nonexistent.json")

        assert result == {}


class TestWriteBaseline:
    """Tests for write_baseline()."""

    def test_writes_file(self, tmp_path):
        """Writes baseline to file."""
        baseline_file = tmp_path / "baseline.json"
        data = {"src/module.py": [{"symbol": "foo", "code": "SUM001"}]}

        write_baseline(data, baseline_file)

        assert baseline_file.exists()
        loaded = json.loads(baseline_file.read_text())
        assert loaded == data

    def test_creates_parent_dirs(self, tmp_path):
        """Creates parent directories if needed."""
        baseline_file = tmp_path / "sub" / "dir" / "baseline.json"

        write_baseline({}, baseline_file)

        assert baseline_file.exists()


class TestGenerateBaseline:
    """Tests for generate_baseline()."""

    def test_generates_from_violations(self, tmp_path):
        """Generates baseline from violations dict."""
        baseline_file = tmp_path / "baseline.json"
        d = _make_diagnostic("SUM001", "my_func")
        violations = {"src/module.py": [d]}

        generate_baseline(violations, baseline_file)

        data = json.loads(baseline_file.read_text())
        assert "src/module.py" in data
        assert data["src/module.py"][0]["code"] == "SUM001"

    def test_skips_empty_symbol(self, tmp_path):
        """Skips violations with empty symbol."""
        baseline_file = tmp_path / "baseline.json"
        d = _make_diagnostic("SUM001", "")
        violations = {"src/module.py": [d]}

        generate_baseline(violations, baseline_file)

        data = json.loads(baseline_file.read_text())
        assert data.get("src/module.py", []) == []


class TestFilterBaselineViolations:
    """Tests for filter_baseline_violations()."""

    def test_filters_known_violations(self):
        """Violations in baseline are filtered out."""
        d = _make_diagnostic("SUM001", "my_func")
        baseline = {"src/module.py": [{"symbol": "my_func", "code": "SUM001"}]}

        result = filter_baseline_violations([d], baseline, "src/module.py")

        assert len(result) == 0

    def test_keeps_new_violations(self):
        """Violations not in baseline are kept."""
        d = _make_diagnostic("SUM002", "my_func")
        baseline = {"src/module.py": [{"symbol": "my_func", "code": "SUM001"}]}

        result = filter_baseline_violations([d], baseline, "src/module.py")

        assert len(result) == 1

    def test_empty_baseline_keeps_all(self):
        """Empty baseline keeps all violations."""
        d = _make_diagnostic("SUM001", "my_func")

        result = filter_baseline_violations([d], {}, "src/module.py")

        assert len(result) == 1


class TestComputeUpdatedBaseline:
    """Tests for compute_updated_baseline()."""

    def test_unchanged_when_same(self):
        """Returns unchanged=False when baseline matches actual violations."""
        baseline = {"src/module.py": [{"symbol": "foo", "code": "SUM001"}]}
        d = _make_diagnostic("SUM001", "foo")
        actual = {"src/module.py": [d]}

        changed, updated = compute_updated_baseline(baseline, actual)

        assert changed is False

    def test_removes_fixed_violation(self):
        """Removes violation that has been fixed."""
        baseline = {
            "src/module.py": [
                {"symbol": "foo", "code": "SUM001"},
                {"symbol": "bar", "code": "SUM002"},
            ]
        }
        d = _make_diagnostic("SUM001", "foo")
        actual = {"src/module.py": [d]}

        changed, updated = compute_updated_baseline(baseline, actual)

        assert changed is True
        assert len(updated["src/module.py"]) == 1
        assert updated["src/module.py"][0]["code"] == "SUM001"
