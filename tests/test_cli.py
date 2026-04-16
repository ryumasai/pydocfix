"""Tests for the CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from pydocfix.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    """Tests for the pydocfix CLI."""

    def test_no_args_shows_help(self, runner):
        """Running with --help shows help."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_check_empty_dir(self, runner, tmp_path):
        """Checking empty directory succeeds with exit code 0."""
        result = runner.invoke(cli, ["check", str(tmp_path)])

        assert result.exit_code == 0

    def test_detects_violation(self, runner, tmp_path):
        """Check command detects violation and exits with code 1."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''\
def greet():
    """Say hello"""
    pass
''')
        result = runner.invoke(cli, ["check", str(tmp_path), "--select", "SUM002"])

        assert result.exit_code == 1
        assert "SUM002" in result.output

    def test_no_violation_exits_zero(self, runner, tmp_path):
        """Check command with no violations exits with code 0."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''\
def greet():
    """Say hello."""
    pass
''')
        result = runner.invoke(cli, ["check", str(tmp_path), "--select", "SUM002"])

        assert result.exit_code == 0

    def test_fix_applies_fix(self, runner, tmp_path):
        """Fix flag applies fix and exits with code 0."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''\
def greet():
    """Say hello"""
    pass
''')
        result = runner.invoke(cli, ["check", "--fix", str(tmp_path), "--select", "SUM002"])

        assert result.exit_code == 0
        assert "hello." in py_file.read_text()

    def test_diff_shows_diff(self, runner, tmp_path):
        """Diff flag shows diff output."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''\
def greet():
    """Say hello"""
    pass
''')
        result = runner.invoke(cli, ["check", "--diff", str(tmp_path), "--select", "SUM002"])

        assert "---" in result.output or "hello." in result.output

    def test_ignore_flag(self, runner, tmp_path):
        """Ignore flag suppresses specific rules."""
        py_file = tmp_path / "example.py"
        py_file.write_text('''\
def greet():
    """Say hello"""
    pass
''')
        result = runner.invoke(cli, ["check", "--ignore", "SUM002", str(tmp_path), "--select", "SUM002"])

        assert result.exit_code == 0

    def test_version_flag(self, runner):
        """Version flag shows version string."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "0." in result.output
