"""Tests for DOC001: Docstring sections not in canonical order."""

from __future__ import annotations

from pydocfix.rules.doc.doc001 import DOC001

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "doc"


class TestDOC001:
    """Test cases for DOC001: section ordering violation."""

    def test_violation_basic(self):
        """Returns section before Args triggers DOC001."""
        fixture = load_fixture("doc001/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [DOC001()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "DOC001"
        assert diagnostics[0].fix is not None

    def test_no_violation(self):
        """Sections in canonical order should not trigger."""
        fixture = load_fixture("doc001/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [DOC001()])

        assert len(diagnostics) == 0

    def test_fix_reorders_sections(self):
        """Auto-fix should put Args before Returns."""
        fixture = load_fixture("doc001/violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [DOC001()], fix=True, unsafe_fixes=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert fixed.index("Args:") < fixed.index("Returns:")

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("doc001/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [DOC001()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [DOC001()])

        assert len(diagnostics2) == 0


class TestDOC001Snapshot:
    """Snapshot tests for DOC001 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix reorders Returns before Args into canonical order."""
        fixture = load_fixture("doc001/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [DOC001()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
