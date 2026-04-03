"""Tests for the CLI module."""

from __future__ import annotations

from click.testing import CliRunner

from pydocfix.cli import cli

runner = CliRunner()


class TestCheck:
    def test_no_args_shows_help(self):
        result = runner.invoke(cli, [])
        assert "check" in result.output

    def test_check_empty_dir(self, tmp_path):
        result = runner.invoke(cli, ["check", str(tmp_path)])
        assert result.exit_code == 0

    def test_check_fix_flag(self, tmp_path):
        result = runner.invoke(cli, ["check", "--fix", str(tmp_path)])
        assert result.exit_code == 0

    def test_check_diff_flag(self, tmp_path):
        result = runner.invoke(cli, ["check", "--diff", str(tmp_path)])
        assert result.exit_code == 0

    def test_check_detects_violation(self, tmp_path):
        p = tmp_path / "bad.py"
        p.write_text('def foo():\n    """No period"""\n    pass\n')
        result = runner.invoke(cli, ["check", str(p)])
        assert result.exit_code == 1
        assert "SUM002" in result.output

    def test_check_fix_applies(self, tmp_path):
        p = tmp_path / "bad.py"
        p.write_text('def foo():\n    """No period"""\n    pass\n')
        result = runner.invoke(cli, ["check", "--fix", str(p)])
        assert result.exit_code == 0
        assert "Fixed" in result.output
        assert '"""No period."""' in p.read_text()

    def test_check_diff_shows_diff(self, tmp_path):
        p = tmp_path / "bad.py"
        p.write_text('def foo():\n    """No period"""\n    pass\n')
        result = runner.invoke(cli, ["check", "--diff", str(p)])
        assert "---" in result.output
        assert "+++" in result.output

    def test_unsafe_fix_not_applied_without_flag(self, tmp_path):
        p = tmp_path / "bad.py"
        p.write_text(
            'def foo(x: int):\n    """Summary.\n\n    Args:\n        x (str): The x value.\n    """\n    pass\n'
        )
        result = runner.invoke(cli, ["check", "--fix", str(p)])
        assert result.exit_code == 1
        assert "unsafe fix" in result.output
        # docstring should NOT be changed
        assert "(str)" in p.read_text()

    def test_unsafe_fix_applied_with_flag(self, tmp_path):
        p = tmp_path / "bad.py"
        p.write_text(
            'def foo(x: int):\n    """Summary.\n\n    Args:\n        x (str): The x value.\n    """\n    pass\n'
        )
        result = runner.invoke(cli, ["check", "--fix", "--unsafe-fixes", str(p)])
        assert "Fixed" in result.output
        assert "(int)" in p.read_text()

    def test_safe_fix_shows_fixable(self, tmp_path):
        p = tmp_path / "bad.py"
        p.write_text('def foo():\n    """No period"""\n    pass\n')
        result = runner.invoke(cli, ["check", str(p)])
        assert "(fixable)" in result.output


class TestCollectFiles:
    def test_excludes_default_dirs(self, tmp_path):
        from pydocfix.cli import _collect_files
        from pydocfix.config import DEFAULT_EXCLUDE

        # .git and __pycache__ should be skipped by default
        for excluded_dir in (".git", "__pycache__", ".tox"):
            d = tmp_path / excluded_dir
            d.mkdir()
            (d / "secret.py").write_text("x = 1\n")

        real = tmp_path / "real.py"
        real.write_text("x = 1\n")

        result = _collect_files([str(tmp_path)], exclude=DEFAULT_EXCLUDE)
        assert real in result
        names = {p.parent.name for p in result}
        assert not names & {".git", "__pycache__", ".tox"}

    def test_exclude_cli_option(self, tmp_path):
        from pydocfix.cli import _collect_files

        skip = tmp_path / "build"
        skip.mkdir()
        (skip / "gen.py").write_text("x = 1\n")
        keep = tmp_path / "src"
        keep.mkdir()
        (keep / "module.py").write_text("x = 1\n")

        result = _collect_files([str(tmp_path)], exclude=frozenset({"build"}))
        paths = [p for p in result]
        assert any(p.parent.name == "src" for p in paths)
        assert not any(p.parent.name == "build" for p in paths)

    def test_exclude_option_via_cli(self, tmp_path):
        skip = tmp_path / "generated"
        skip.mkdir()
        bad = skip / "bad.py"
        bad.write_text('def foo():\n    """No period"""\n    pass\n')

        result = runner.invoke(cli, ["check", "--exclude", "generated", str(tmp_path)])
        assert result.exit_code == 0
