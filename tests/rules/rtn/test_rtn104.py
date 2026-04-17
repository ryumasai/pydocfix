"""Tests for RTN104: Redundant return type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability, build_registry
from pydocfix.rules.rtn.rtn104 import RTN104

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN104:
    """Test cases for RTN104."""

    def _rule(self) -> RTN104:
        return RTN104(Config(type_annotation_style="signature"))

    def test_violation_basic(self):
        """Returns entry with docstring type redundant with signature triggers RTN104."""
        fixture = load_fixture("rtn104/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN104"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Returns entry with no docstring type should not trigger."""
        fixture = load_fixture("rtn104/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("rtn104/violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["RTN103", "RTN104"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "RTN103" not in codes
        assert "RTN104" not in codes

    def test_fix_removes_return_type(self):
        """Auto-fix should remove the type from the docstring return entry."""
        fixture = load_fixture("rtn104/violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [self._rule()], fix=True)

        assert fixed is not None
        # The Returns section type annotation should be removed
        # Count "int:" occurrences - fixed should have fewer than original
        assert fixed.count("int:") < original.count("int:")
