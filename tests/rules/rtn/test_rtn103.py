"""Tests for RTN103: Return has no type in docstring (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability, build_registry
from pydocfix.rules.rtn.rtn103 import RTN103

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN103:
    """Test cases for RTN103."""

    def _rule(self) -> RTN103:
        return RTN103(Config(type_annotation_style="docstring"))

    def test_violation_basic(self):
        """Returns entry with no docstring type in docstring style triggers RTN103."""
        fixture = load_fixture("rtn103_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN103"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Returns entry with docstring type should not trigger."""
        fixture = load_fixture("rtn103_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("rtn103_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["RTN103", "RTN104"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "RTN103" not in codes
        assert "RTN104" not in codes
