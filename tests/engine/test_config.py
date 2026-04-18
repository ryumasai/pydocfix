"""Tests for config loading."""

from __future__ import annotations

from pydocfix.config import Config, find_pyproject_toml, load_config


class TestConfig:
    """Tests for Config dataclass."""

    def test_defaults(self):
        """Config has expected defaults."""
        config = Config()

        assert config.skip_short_docstrings is True
        assert config.type_annotation_style is None
        assert config.ignore == []
        assert config.select == []

    def test_custom_values(self):
        """Config accepts custom values."""
        config = Config(
            skip_short_docstrings=False,
            type_annotation_style="signature",
            ignore=["SUM001"],
        )

        assert config.skip_short_docstrings is False
        assert config.type_annotation_style == "signature"
        assert "SUM001" in config.ignore


class TestFindPyprojectToml:
    """Tests for find_pyproject_toml()."""

    def test_finds_file(self, tmp_path):
        """Finds pyproject.toml in the start directory."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[tool.pydocfix]\n")

        result = find_pyproject_toml(tmp_path)

        assert result == toml

    def test_finds_ancestor(self, tmp_path):
        """Finds pyproject.toml in parent directory."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[tool.pydocfix]\n")
        sub = tmp_path / "sub"
        sub.mkdir()

        result = find_pyproject_toml(sub)

        assert result == toml

    def test_returns_none_if_missing(self, tmp_path):
        """Returns None if no pyproject.toml found."""
        result = find_pyproject_toml(tmp_path)

        assert result is None


class TestLoadConfig:
    """Tests for load_config()."""

    def test_loads_ignore(self, tmp_path):
        """load_config reads ignore list."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text('[tool.pydocfix]\nignore = ["SUM001"]\n')

        config = load_config(tmp_path)

        assert "SUM001" in config.ignore

    def test_loads_select(self, tmp_path):
        """load_config reads select list."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text('[tool.pydocfix]\nselect = ["SUM002"]\n')

        config = load_config(tmp_path)

        assert "SUM002" in config.select

    def test_loads_skip_short_docstrings(self, tmp_path):
        """load_config reads skip_short_docstrings."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[tool.pydocfix]\nskip_short_docstrings = false\n")

        config = load_config(tmp_path)

        assert config.skip_short_docstrings is False

    def test_loads_type_annotation_style(self, tmp_path):
        """load_config reads type_annotation_style."""
        toml = tmp_path / "pyproject.toml"
        toml.write_text('[tool.pydocfix]\ntype_annotation_style = "signature"\n')

        config = load_config(tmp_path)

        assert config.type_annotation_style == "signature"

    def test_defaults_when_no_file(self, tmp_path):
        """load_config returns defaults when no pyproject.toml."""
        config = load_config(tmp_path)

        assert config.skip_short_docstrings is True
        assert config.type_annotation_style is None
