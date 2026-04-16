"""Tests for PRM002: Function has no parameters but docstring has Args section."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm002 import PRM002

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM002:
    """Test cases for PRM002."""

    def test_violation_basic(self):
        """Function with no params but Args section triggers PRM002."""
        fixture = load_fixture("prm002_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM002()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM002"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Function with params and Args section, or no params and no Args, should not trigger."""
        fixture = load_fixture("prm002_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM002()])

        assert len(diagnostics) == 0

    def test_fix_removes_args_section(self):
        """Auto-fix should remove the Args section."""
        fixture = load_fixture("prm002_violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [PRM002()], fix=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert "Args:" not in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm002_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM002()], fix=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM002()])

        assert len(diagnostics2) == 0


class TestPRM002Snapshot:
    """Snapshot tests for PRM002 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix removes the extraneous Args section."""
        fixture = load_fixture("prm002_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM002()], fix=True)

        assert fixed is not None
        assert fixed == snapshot
