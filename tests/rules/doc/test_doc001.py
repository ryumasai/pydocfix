"""Tests for DOC001: Docstring sections not in canonical order."""

from __future__ import annotations

from pydocfix.rules.doc.doc001 import doc001

from ..conftest import check_rule, load_fixture

CATEGORY = "doc"


class TestDOC001:
    def _rules(self):
        return [doc001]

    def test_rule(self, snapshot):
        fixture = load_fixture("doc001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="doc001.py", unsafe_fixes=True) == snapshot
