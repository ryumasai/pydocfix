"""Tests for SUM002: Summary should end with a period."""

from __future__ import annotations

from pydocfix.rules.sum.sum002 import SUM002

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "sum"


class TestSUM002:
    """Test cases for SUM002: summary missing terminal punctuation."""

    def test_violation_basic(self):
        """Single-line docstring without period triggers SUM002."""
        fixture = load_fixture("sum002/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [SUM002()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SUM002"
        assert diagnostics[0].fix is not None

    def test_violation_multiline(self):
        """Multiline docstring with summary missing period triggers SUM002."""
        fixture = load_fixture("sum002/violation_multiline.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [SUM002()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SUM002"

    def test_no_violation(self):
        """Summaries ending with .!? should not trigger."""
        fixture = load_fixture("sum002/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [SUM002()])

        assert len(diagnostics) == 0

    def test_fix_available(self):
        """Auto-fix should append a period."""
        fixture = load_fixture("sum002/violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [SUM002()], fix=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert fixed != original
        assert '"""Do something."""' in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice should produce no further violations."""
        fixture = load_fixture("sum002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [SUM002()], fix=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, fixed2, _ = check_fixture_file(temp, [SUM002()])

        assert len(diagnostics2) == 0
        assert fixed2 is None


class TestSUM002Snapshot:
    """Snapshot tests for SUM002 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Basic fix appends a period to the summary."""
        fixture = load_fixture("sum002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [SUM002()], fix=True)

        assert fixed is not None
        assert fixed == snapshot

    def test_fix_multiline(self, snapshot):
        """Fix on multiline docstring preserves sections."""
        fixture = load_fixture("sum002/violation_multiline.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [SUM002()], fix=True)

        assert fixed is not None
        assert fixed == snapshot
