"""Tests for YLD104: Redundant yield type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability, build_registry
from pydocfix.rules.yld.yld104 import YLD104

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD104:
    """Test cases for YLD104."""

    def _rule(self) -> YLD104:
        return YLD104(Config(type_annotation_style="signature"))

    def test_violation_basic(self):
        """Yields entry with redundant docstring type in signature style triggers YLD104."""
        fixture = load_fixture("yld104/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD104"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Yields entry with no docstring type should not trigger."""
        fixture = load_fixture("yld104/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("yld104/violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["YLD103", "YLD104"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "YLD103" not in codes
        assert "YLD104" not in codes

    def test_fix_removes_yield_type(self):
        """Auto-fix should remove the type from the docstring yields entry."""
        fixture = load_fixture("yld104/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [self._rule()], fix=True)

        assert fixed is not None
        assert "int:" not in fixed


class TestYLD104Snapshot:
    """Snapshot tests for YLD104 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Snapshot test for YLD104 fix."""
        fixture = load_fixture("yld104/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [YLD104(Config(type_annotation_style="signature"))], fix=True)
        assert fixed == snapshot
