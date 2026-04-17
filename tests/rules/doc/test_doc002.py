"""Tests for DOC002: Incorrect indentation of docstring entry."""

from __future__ import annotations

from pydocfix.rules.doc.doc002 import DOC002

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "doc"


class TestDOC002:
    """Test cases for DOC002: entry indentation violation."""

    def test_violation_basic(self):
        """Under-indented entry triggers DOC002."""
        fixture = load_fixture("doc002/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [DOC002()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "DOC002"
        assert diagnostics[0].fix is not None

    def test_no_violation(self):
        """Correctly indented entries should not trigger."""
        fixture = load_fixture("doc002/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [DOC002()])

        assert len(diagnostics) == 0

    def test_fix_corrects_indentation(self):
        """Auto-fix should correct the entry indentation."""
        fixture = load_fixture("doc002/violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [DOC002()], fix=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert fixed != original

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("doc002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [DOC002()], fix=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [DOC002()])

        assert len(diagnostics2) == 0


class TestDOC002Snapshot:
    """Snapshot tests for DOC002 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix corrects indentation to expected level."""
        fixture = load_fixture("doc002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [DOC002()], fix=True)

        assert fixed is not None
        assert fixed == snapshot
