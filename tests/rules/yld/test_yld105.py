"""Tests for YLD105: Yield has no annotation in signature (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import build_registry
from pydocfix.rules.yld.yld105 import YLD105

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD105:
    """Test cases for YLD105."""

    def _rule(self) -> YLD105:
        return YLD105(Config(type_annotation_style="signature"))

    def test_violation_basic(self):
        """Yields entry without signature annotation in signature style triggers YLD105."""
        fixture = load_fixture("yld105/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD105"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Yields entry with signature annotation should not trigger."""
        fixture = load_fixture("yld105/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_not_active_without_config(self):
        """Rule should not fire when conflicting rules present and no config."""
        from pydocfix.checker import check_file

        fixture = load_fixture("yld105/violation_basic.py", CATEGORY)
        source = fixture.read_text()
        registry = build_registry(select=["YLD105", "YLD106"], config=Config())
        type_to_rules = registry.type_to_rules
        diagnostics, _, _ = check_file(source, fixture, type_to_rules, config=Config())

        codes = {d.rule for d in diagnostics}
        assert "YLD105" not in codes
        assert "YLD106" not in codes
