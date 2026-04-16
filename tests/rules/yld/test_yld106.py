"""Tests for YLD106: Yield has signature annotation (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import build_registry
from pydocfix.rules.yld.yld106 import YLD106

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD106:
    """Test cases for YLD106."""

    def _rule(self) -> YLD106:
        return YLD106(Config(type_annotation_style="docstring"))

    def test_violation_basic(self):
        """Generator function with signature annotation in docstring style triggers YLD106."""
        fixture = load_fixture("yld106_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD106"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Generator without signature annotation should not trigger."""
        fixture = load_fixture("yld106_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("yld106_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["YLD105", "YLD106"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "YLD105" not in codes
        assert "YLD106" not in codes
