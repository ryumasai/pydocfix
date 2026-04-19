"""Tests for baseline read/write/filter."""

from __future__ import annotations

import json
import logging

from pydocfix.engine.baseline import (
    compute_updated_baseline,
    filter_baseline_violations,
    generate_baseline,
    load_baseline,
    normalize_path,
    write_baseline,
)


class TestNormalizePath:
    """normalize_path()."""

    def test_returns_relative_posix_path(self, tmp_path):
        """file under root returns a relative POSIX-style path string."""
        file = tmp_path / "src" / "module.py"
        file.parent.mkdir(parents=True)
        file.touch()

        result = normalize_path(file, tmp_path)

        assert result == "src/module.py"

    def test_outside_root_returns_absolute(self, tmp_path):
        """file outside root returns its absolute path as a string."""
        outside = tmp_path.parent / "other.py"
        outside.touch()

        result = normalize_path(outside, tmp_path)

        assert result == str(outside.resolve())


class TestLoadBaseline:
    """load_baseline()."""

    def test_missing_file_returns_empty_dict(self, tmp_path):
        """returns {} when the baseline file does not exist."""
        result = load_baseline(tmp_path / "nonexistent.json")

        assert result == {}

    def test_broken_json_returns_empty_dict(self, tmp_path, caplog):
        """returns {} and logs a warning for invalid JSON."""
        bad = tmp_path / "baseline.json"
        bad.write_text("NOT JSON")

        with caplog.at_level(logging.WARNING):
            result = load_baseline(bad)

        assert result == {}
        assert caplog.records

    def test_non_dict_json_returns_empty_dict(self, tmp_path, caplog):
        """returns {} and logs a warning when JSON root is not a dict."""
        bad = tmp_path / "baseline.json"
        bad.write_text('["not", "a", "dict"]')

        with caplog.at_level(logging.WARNING):
            result = load_baseline(bad)

        assert result == {}
        assert caplog.records


class TestWriteBaseline:
    """write_baseline()."""

    def test_writes_and_reads_back(self, tmp_path):
        """written data can be read back as valid JSON."""
        path = tmp_path / "baseline.json"
        data = {"src/module.py": [{"symbol": "my_func", "code": "SUM001"}]}

        write_baseline(data, path)

        assert json.loads(path.read_text()) == data

    def test_creates_parent_directories(self, tmp_path):
        """parent directories are created automatically."""
        path = tmp_path / "sub" / "dir" / "baseline.json"

        write_baseline({}, path)

        assert path.exists()


class TestGenerateBaseline:
    """generate_baseline() with real Diagnostic objects."""

    def test_writes_entry_for_diagnostic_with_symbol(self, tmp_path, make_diagnostic):
        """diagnostic with non-empty symbol is written to baseline."""
        d = make_diagnostic("SUM001", symbol="my_func")
        path = tmp_path / "baseline.json"

        generate_baseline({"src/module.py": [d]}, path)

        data = json.loads(path.read_text())
        assert data["src/module.py"] == [{"symbol": "my_func", "code": "SUM001"}]

    def test_skips_diagnostic_with_empty_symbol(self, tmp_path, make_diagnostic):
        """diagnostic with empty symbol is excluded from baseline."""
        d = make_diagnostic("SUM001", symbol="")
        path = tmp_path / "baseline.json"

        generate_baseline({"src/module.py": [d]}, path)

        data = json.loads(path.read_text())
        assert data.get("src/module.py", []) == []


class TestFilterBaselineViolations:
    """filter_baseline_violations()."""

    def test_filters_known_and_keeps_new(self, make_diagnostic):
        """violation in baseline is removed; new violation is kept."""
        d_known = make_diagnostic("SUM001", symbol="my_func")
        d_new = make_diagnostic("SUM002", symbol="my_func")
        baseline = {"src/module.py": [{"symbol": "my_func", "code": "SUM001"}]}

        result = filter_baseline_violations([d_known, d_new], baseline, "src/module.py")

        assert len(result) == 1
        assert result[0].rule == "SUM002"

    def test_empty_baseline_returns_all(self, make_diagnostic):
        """empty baseline passes all diagnostics through unchanged."""
        d = make_diagnostic("SUM001", symbol="my_func")

        result = filter_baseline_violations([d], {}, "src/module.py")

        assert result == [d]


class TestComputeUpdatedBaseline:
    """compute_updated_baseline()."""

    def test_fixed_violation_is_removed(self, make_diagnostic):
        """violation absent from actual run is removed; changed=True."""
        baseline = {
            "src/module.py": [
                {"symbol": "foo", "code": "SUM001"},
                {"symbol": "bar", "code": "SUM002"},
            ]
        }
        # Only "foo/SUM001" still present; "bar/SUM002" is fixed
        d = make_diagnostic("SUM001", symbol="foo")
        actual = {"src/module.py": [d]}

        changed, updated = compute_updated_baseline(baseline, actual)

        assert changed is True

    def test_unchanged_baseline_returns_false(self, make_diagnostic):
        """identical actual results return changed=False."""
        baseline = {"src/module.py": [{"symbol": "foo", "code": "SUM001"}]}
        d = make_diagnostic("SUM001", symbol="foo")
        actual = {"src/module.py": [d]}

        changed, updated = compute_updated_baseline(baseline, actual)

        assert changed is False
        assert len(updated["src/module.py"]) == 1
        assert updated["src/module.py"][0]["code"] == "SUM001"
