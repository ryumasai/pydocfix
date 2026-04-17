"""Tests for PRM001: Function has parameters but no Args/Parameters section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm001 import PRM001

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM001:
    """Test cases for PRM001."""

    def _rule(self) -> PRM001:
        return PRM001(Config(skip_short_docstrings=False))

    def test_violation_basic(self):
        """Function with params but no Args section triggers PRM001."""
        fixture = load_fixture("prm001/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) >= 1
        assert diagnostics[0].rule == "PRM001"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Function with Args section or no params should not trigger."""
        fixture = load_fixture("prm001/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_fix_adds_args_section(self):
        """Auto-fix should add an Args section."""
        fixture = load_fixture("prm001/violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [self._rule()], fix=True, unsafe_fixes=True)

        assert len(diagnostics) >= 1
        assert fixed is not None
        assert fixed != original
        assert "Args:" in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm001/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [self._rule()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [self._rule()])

        assert len(diagnostics2) == 0


class TestPRM001Snapshot:
    """Snapshot tests for PRM001 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix adds Args section with parameter stubs."""
        fixture = load_fixture("prm001/violation_basic.py", CATEGORY)
        rule = PRM001(Config(skip_short_docstrings=False))
        _, fixed, _ = check_fixture_file(fixture, [rule], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
