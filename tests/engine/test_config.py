"""Tests for configuration loading."""

from __future__ import annotations

import logging

from pydocfix.config import Config, load_config


class TestConfigDefaults:
    """Config dataclass default values."""

    def test_skip_short_docstrings_default(self):
        """skip_short_docstrings defaults to True."""
        assert Config().skip_short_docstrings is True

    def test_list_fields_default_empty(self):
        """ignore, select, exclude default to empty list."""
        config = Config()

        assert config.ignore == []
        assert config.select == []
        assert config.exclude == []

    def test_fix_extension_fields_default_empty(self):
        """extend_safe_fixes and extend_unsafe_fixes default to empty list."""
        config = Config()

        assert config.extend_safe_fixes == []
        assert config.extend_unsafe_fixes == []

    def test_type_annotation_style_default_none(self):
        """type_annotation_style defaults to None."""
        assert Config().type_annotation_style is None

    def test_preferred_style_default(self):
        """preferred_style defaults to 'google'."""
        assert Config().preferred_style == "google"

    def test_output_format_default(self):
        """output_format defaults to 'full'."""
        assert Config().output_format == "full"

    def test_baseline_default_none(self):
        """baseline defaults to None."""
        assert Config().baseline is None


class TestLoadConfig:
    """load_config() reads pyproject.toml values."""

    def test_loads_ignore_and_select(self, tmp_path):
        """ignore and select are loaded from TOML."""
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nignore = ["SUM001"]\nselect = ["PRM001"]\n')

        config = load_config(tmp_path)

        assert "SUM001" in config.ignore
        assert "PRM001" in config.select

    def test_loads_extend_safe_and_unsafe_fixes(self, tmp_path):
        """extend-safe-fixes and extend-unsafe-fixes are loaded and uppercased."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.pydocfix]\nextend-safe-fixes = ["prm001"]\nextend-unsafe-fixes = ["RTN101"]\n'
        )

        config = load_config(tmp_path)

        assert "PRM001" in config.extend_safe_fixes
        assert "RTN101" in config.extend_unsafe_fixes

    def test_invalid_type_annotation_style_falls_back(self, tmp_path, caplog):
        """invalid type_annotation_style falls back to None with a warning."""
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\ntype_annotation_style = "invalid"\n')

        with caplog.at_level(logging.WARNING):
            config = load_config(tmp_path)

        assert config.type_annotation_style is None
        assert any("type_annotation_style" in r.message for r in caplog.records)

    def test_invalid_preferred_style_falls_back(self, tmp_path, caplog):
        """invalid preferred_style falls back to 'google' with a warning."""
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\npreferred_style = "invalid"\n')

        with caplog.at_level(logging.WARNING):
            config = load_config(tmp_path)

        assert config.preferred_style == "google"
        assert any("preferred_style" in r.message for r in caplog.records)

    def test_no_pyproject_toml_returns_defaults(self, tmp_path):
        """missing pyproject.toml returns default Config."""
        config = load_config(tmp_path)

        assert config.skip_short_docstrings is True
        assert config.ignore == []

    def test_missing_section_returns_defaults(self, tmp_path):
        """pyproject.toml without [tool.pydocfix] returns default Config."""
        (tmp_path / "pyproject.toml").write_text("[tool.other]\nkey = 1\n")

        config = load_config(tmp_path)

        assert config.ignore == []
        assert config.select == []

    def test_finds_ancestor_pyproject_toml(self, tmp_path):
        """load_config walks up to find pyproject.toml in a parent directory."""
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nignore = ["SUM001"]\n')
        sub = tmp_path / "sub" / "dir"
        sub.mkdir(parents=True)

        config = load_config(sub)

        assert "SUM001" in config.ignore
