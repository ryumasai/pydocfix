"""Tests for DOC003: One-line docstring should be written on a single line."""

from __future__ import annotations

from pydocfix.rules.doc.doc003 import doc003

from ..conftest import check_rule, load_fixture

CATEGORY = "doc"


class TestDOC003:
    def _rules(self):
        return [doc003]

    def test_rule(self, snapshot):
        fixture = load_fixture("doc003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="doc003.py") == snapshot
