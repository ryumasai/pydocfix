"""Tests for file collection."""

from __future__ import annotations

from pydocfix._filewalker import collect_files


class TestCollectFiles:
    """collect_files()."""

    def test_collects_py_and_pyi_excludes_txt(self, tmp_path):
        """.py and .pyi files are collected; .txt is not."""
        (tmp_path / "a.py").touch()
        (tmp_path / "b.pyi").touch()
        (tmp_path / "c.txt").touch()

        result = collect_files([str(tmp_path)])
        names = {p.name for p in result}

        assert "a.py" in names
        assert "b.pyi" in names
        assert "c.txt" not in names

    def test_deduplicates_overlapping_paths(self, tmp_path):
        """passing a dir and its parent does not produce duplicate paths."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "module.py").touch()

        result = collect_files([str(tmp_path), str(sub)])

        py_files = [p for p in result if p.name == "module.py"]
        assert len(py_files) == 1

    def test_exclude_simple_name(self, tmp_path):
        """a directory matching a simple exclude name is skipped."""
        hidden = tmp_path / "__pycache__"
        hidden.mkdir()
        (hidden / "cached.py").touch()
        (tmp_path / "module.py").touch()

        result = collect_files([str(tmp_path)], exclude=frozenset({"__pycache__"}))
        names = {p.name for p in result}

        assert "cached.py" not in names
        assert "module.py" in names

    def test_exclude_glob_pattern(self, tmp_path):
        """a glob pattern in exclude skips matching nested paths."""
        fixtures = tmp_path / "tests" / "fixtures"
        fixtures.mkdir(parents=True)
        (fixtures / "fix.py").touch()
        (tmp_path / "src.py").touch()

        result = collect_files(
            [str(tmp_path)],
            exclude=frozenset({"tests/**/fixtures"}),
            root=tmp_path,
        )
        names = {p.name for p in result}

        assert "fix.py" not in names
        assert "src.py" in names

    def test_nonexistent_path_returns_empty(self, tmp_path, caplog):
        """a path that does not exist produces a warning and no files."""
        import logging

        with caplog.at_level(logging.WARNING):
            result = collect_files([str(tmp_path / "nonexistent")])

        assert result == []
        assert any("nonexistent" in r.message for r in caplog.records)

    def test_single_file_path_is_collected(self, tmp_path):
        """a direct .py file path is collected without walking a directory."""
        f = tmp_path / "standalone.py"
        f.touch()

        result = collect_files([str(f)])

        assert any(p.name == "standalone.py" for p in result)

    def test_empty_paths_returns_empty(self):
        """passing an empty list returns an empty result."""
        result = collect_files([])

        assert result == []
