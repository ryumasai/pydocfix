"""Tests for SUM001: Docstring has no summary line."""

from __future__ import annotations

from pydocfix.rules.sum.sum001 import SUM001

from ..conftest import check_rule, load_fixture

CATEGORY = "sum"


class TestSUM001:
    def _rules(self):
        return [SUM001()]

    def test_rule(self, snapshot):
        fixture = load_fixture("sum001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="sum001.py") == snapshot
