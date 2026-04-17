"""Tests for DOC002: Incorrect indentation of docstring entry."""

from __future__ import annotations

from pydocfix.rules.doc.doc002 import DOC002

from ..conftest import check_rule, load_fixture

CATEGORY = "doc"


class TestDOC002:
    def _rules(self):
        return [DOC002()]

    def test_rule(self, snapshot):
        fixture = load_fixture("doc002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="doc002.py") == snapshot
