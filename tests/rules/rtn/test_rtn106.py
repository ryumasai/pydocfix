"""Tests for RTN106: Return has signature annotation (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import build_registry
from pydocfix.rules.rtn.rtn106 import RTN106

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN106:
    """Test cases for RTN106."""

    def _rule(self) -> RTN106:
        return RTN106(Config(type_annotation_style="docstring"))

    def test_violation_basic(self):
        """Function with return annotation in docstring style triggers RTN106."""
        fixture = load_fixture("rtn106_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN106"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Function without return annotation should not trigger."""
        fixture = load_fixture("rtn106_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("rtn106_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["RTN105", "RTN106"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "RTN105" not in codes
        assert "RTN106" not in codes
