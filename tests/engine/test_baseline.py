"""Tests for baseline read/write/filter — F-1 to F-9."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydocfix.baseline import (
    compute_updated_baseline,
    filter_baseline_violations,
    generate_baseline,
    load_baseline,
    normalize_path,
    write_baseline,
)


class TestNormalizePath:
    """F-1: normalize_path()."""

    def test_returns_relative_posix_path(self, tmp_path):
        """F-1: file under root returns a relative POSIX-style path string."""
        file = tmp_path / "src" / "module.py"
        file.parent.mkdir(parents=True)
        file.touch()

        result = normalize_path(file, tmp_path)

        assert result == "src/module.py"


class TestLoadBaseline:
    """F-2, F-3: load_baseline()."""

    def test_missing_file_returns_empty_dict(self, tmp_path):
        """F-2: returns {} when the baseline file does not exist."""
        result = load_baseline(tmp_path / "nonexistent.json")

        assert result == {}

    def test_broken_json_returns_empty_dict(self, tmp_path, caplog):
        """F-3: returns {} and logs a warning for invalid JSON."""
        bad = tmp_path / "baseline.json"
        bad.write_text("NOT JSON")

        with caplog.at_level(logging.WARNING):
            result = load_baseline(bad)

        assert result == {}
        assert caplog.records


class TestWriteBaseline:
    """F-4, F-5: write_baseline()."""

    def test_writes_and_reads_back(self, tmp_path):
        """F-4: written data can be read back as valid JSON."""
        path = tmp_path / "baseline.json"
        data = {"src/module.py": [{"symbol": "my_func", "code": "SUM001"}]}

        write_baseline(data, path)

        assert json.loads(path.read_text()) == data

    def test_creates_parent_directories(self, tmp_path):
        """F-5: parent directories are created automatically."""
        path = tmp_path / "sub" / "dir" / "baseline.json"

        write_baseline({}, path)

        assert path.exists()


class TestGenerateBaseline:
    """F-6, F-7: generate_baseline() with real Diagnostic objects."""

    def test_writes_entry_for_diagnostic_with_symbol(self, tmp_path, make_diagnostic):
        """F-6: diagnostic with non-empty symbol is written to baseline."""
        d = make_diagnostic("SUM001", symbol="my_func")
        path = tmp_path / "baseline.json"

        generate_baseline({"src/module.py": [d]}, path)

        data = json.loads(path.read_text())
        assert data["src/module.py"] == [{"symbol": "my_func", "code": "SUM001"}]

    def test_skips_diagnostic_with_empty_symbol(self, tmp_path, make_diagnostic):
        """F-7: diagnostic with empty symbol is excluded from baseline."""
        d = make_diagnostic("SUM001", symbol="")
        path = tmp_path / "baseline.json"

        generate_baseline({"src/module.py": [d]}, path)

        data = json.loads(path.read_text())
        assert data.get("src/module.py", []) == []


class TestFilterBaselineViolations:
    """F-8: filter_baseline_violations()."""

    def test_filters_known_and_keeps_new(self, make_diagnostic):
        """F-8: violation in baseline is removed; new violation is kept."""
        d_known = make_diagnostic("SUM001", symbol="my_func")
        d_new = make_diagnostic("SUM002", symbol="my_func")
        baseline = {"src/module.py": [{"symbol": "my_func", "code": "SUM001"}]}

        result = filter_baseline_violations([d_known, d_new], baseline, "src/module.py")

        assert len(result) == 1
        assert result[0].rule == "SUM002"


class TestComputeUpdatedBaseline:
    """F-9: compute_updated_baseline()."""

    def test_fixed_violation_is_removed(self, make_diagnostic):
        """F-9: violation absent from actual run is removed; changed=True."""
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
        assert len(updated["src/module.py"]) == 1
        assert updated["src/module.py"][0]["code"] == "SUM001"
