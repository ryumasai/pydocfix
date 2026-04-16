"""Tests for PRM105: Parameter has no signature annotation (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import build_registry
from pydocfix.rules.prm.prm105 import PRM105

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM105:
    """Test cases for PRM105."""

    def _rule(self) -> PRM105:
        return PRM105(Config(type_annotation_style="signature"))

    def test_violation_basic(self):
        """Documented parameter without signature annotation triggers PRM105."""
        fixture = load_fixture("prm105_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM105"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Parameter with signature annotation should not trigger."""
        fixture = load_fixture("prm105_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rules present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("prm105_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["PRM105", "PRM106"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "PRM105" not in codes
        assert "PRM106" not in codes
