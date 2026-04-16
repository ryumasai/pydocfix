"""Tests for PRM103: Parameter has no type in docstring (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability, build_registry
from pydocfix.rules.prm.prm103 import PRM103

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM103:
    """Test cases for PRM103."""

    def _rule(self) -> PRM103:
        return PRM103(Config(type_annotation_style="docstring"))

    def test_violation_basic(self):
        """Parameter lacking docstring type with docstring style triggers PRM103."""
        fixture = load_fixture("prm103_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM103"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Parameter with docstring type should not trigger."""
        fixture = load_fixture("prm103_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("prm103_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["PRM103", "PRM104"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        # Neither PRM103 nor PRM104 should fire without type_annotation_style
        codes = {d.rule for d in diagnostics}
        assert "PRM103" not in codes
        assert "PRM104" not in codes

    def test_fix_inserts_type(self):
        """Auto-fix should insert the type from signature into docstring."""
        fixture = load_fixture("prm103_violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [self._rule()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "(int)" in fixed
