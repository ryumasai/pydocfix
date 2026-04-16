"""Tests for PRM104: Redundant type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability, build_registry
from pydocfix.rules.prm.prm104 import PRM104

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM104:
    """Test cases for PRM104."""

    def _rule(self) -> PRM104:
        return PRM104(Config(type_annotation_style="signature"))

    def test_violation_basic(self):
        """Docstring type redundant with signature annotation triggers PRM104."""
        fixture = load_fixture("prm104_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM104"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Parameter with no docstring type should not trigger."""
        fixture = load_fixture("prm104_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("prm104_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["PRM103", "PRM104"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "PRM103" not in codes
        assert "PRM104" not in codes

    def test_fix_removes_type(self):
        """Auto-fix should remove the type from the docstring entry."""
        fixture = load_fixture("prm104_violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [self._rule()], fix=True)

        assert fixed is not None
        assert "(int)" not in fixed
        assert "x:" in fixed
