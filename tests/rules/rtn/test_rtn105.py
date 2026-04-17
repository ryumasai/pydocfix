"""Tests for RTN105: Return has no annotation in signature (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import build_registry
from pydocfix.rules.rtn.rtn105 import RTN105

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN105:
    """Test cases for RTN105."""

    def _rule(self) -> RTN105:
        return RTN105(Config(type_annotation_style="signature"))

    def test_violation_basic(self):
        """Returns entry without signature annotation in signature style triggers RTN105."""
        fixture = load_fixture("rtn105/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN105"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Returns entry with signature annotation should not trigger."""
        fixture = load_fixture("rtn105/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rules present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("rtn105/violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["RTN105", "RTN106"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "RTN105" not in codes
        assert "RTN106" not in codes
