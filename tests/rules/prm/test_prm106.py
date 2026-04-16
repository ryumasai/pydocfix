"""Tests for PRM106: Parameter has signature annotation (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import build_registry
from pydocfix.rules.prm.prm106 import PRM106

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM106:
    """Test cases for PRM106."""

    def _rule(self) -> PRM106:
        return PRM106(Config(type_annotation_style="docstring"))

    def test_violation_basic(self):
        """Documented parameter with signature annotation triggers PRM106 in docstring style."""
        fixture = load_fixture("prm106_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM106"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Parameter without signature annotation should not trigger."""
        fixture = load_fixture("prm106_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("prm106_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["PRM105", "PRM106"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "PRM105" not in codes
        assert "PRM106" not in codes
