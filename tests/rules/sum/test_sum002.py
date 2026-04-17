"""Tests for SUM002: Summary should end with a period."""

from __future__ import annotations

from pydocfix.rules.sum.sum002 import SUM002

from ..conftest import check_rule, load_fixture

CATEGORY = "sum"


class TestSUM002:
    def _rules(self):
        return [SUM002()]

    def test_rule(self, snapshot):
        fixture = load_fixture("sum002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="sum002.py") == snapshot
