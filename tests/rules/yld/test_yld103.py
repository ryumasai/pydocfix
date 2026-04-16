"""Tests for YLD103: Yield has no type in docstring (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability, build_registry
from pydocfix.rules.yld.yld103 import YLD103

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD103:
    """Test cases for YLD103."""

    def _rule(self) -> YLD103:
        return YLD103(Config(type_annotation_style="docstring"))

    def test_violation_basic(self):
        """Yields entry with no docstring type in docstring style triggers YLD103."""
        fixture = load_fixture("yld103_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD103"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Yields entry with docstring type should not trigger."""
        fixture = load_fixture("yld103_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rule present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("yld103_violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["YLD103", "YLD104"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "YLD103" not in codes
        assert "YLD104" not in codes
