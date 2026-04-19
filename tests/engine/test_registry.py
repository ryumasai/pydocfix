"""Tests for RuleRegistry and applicability helpers — C-1 to C-11."""

from __future__ import annotations

import pytest
from pydocstring import GoogleDocstring

from pydocfix.config import Config
from pydocfix.models import Applicability, Diagnostic, Fix, Offset, Range
from pydocfix.registry import RuleRegistry, effective_applicability, is_applicable
from tests.engine._rules.safe001 import SAFE001
from tests.engine._rules.unsafe001 import UNSAFE001
from tests.helpers import make_registry


def _diag(rule: str, applicability: Applicability | None = None) -> Diagnostic:
    """Create a minimal Diagnostic, optionally with a Fix."""
    fix = Fix(edits=[], applicability=applicability) if applicability is not None else None
    return Diagnostic(
        rule=rule,
        message="test",
        filepath="test.py",
        range=Range(start=Offset(1, 1), end=Offset(1, 10)),
        fix=fix,
    )


class TestEffectiveApplicability:
    """C-1 to C-4, C-7: effective_applicability()."""

    def test_raises_when_fix_is_none(self):
        """C-1: ValueError when diagnostic has no fix."""
        d = _diag("SAFE001")

        with pytest.raises(ValueError):
            effective_applicability(d)

    def test_returns_original_applicability_without_config(self):
        """C-2: returns fix.applicability unchanged when config is None."""
        d = _diag("SAFE001", Applicability.UNSAFE)

        assert effective_applicability(d) == Applicability.UNSAFE

    def test_extend_safe_fixes_promotes_to_safe(self):
        """C-3: UNSAFE fix is promoted to SAFE via extend_safe_fixes."""
        d = _diag("SAFE001", Applicability.UNSAFE)
        config = Config(extend_safe_fixes=["SAFE001"])

        assert effective_applicability(d, config) == Applicability.SAFE

    def test_extend_unsafe_fixes_demotes_to_unsafe(self):
        """C-4: SAFE fix is demoted to UNSAFE via extend_unsafe_fixes."""
        d = _diag("SAFE001", Applicability.SAFE)
        config = Config(extend_unsafe_fixes=["SAFE001"])

        assert effective_applicability(d, config) == Applicability.UNSAFE

    def test_prefix_matching_in_extend_safe_fixes(self):
        """C-7: prefix 'SAFE' in extend_safe_fixes promotes SAFE001."""
        d = _diag("SAFE001", Applicability.UNSAFE)
        config = Config(extend_safe_fixes=["SAFE"])

        assert effective_applicability(d, config) == Applicability.SAFE


class TestIsApplicable:
    """C-5, C-6: is_applicable()."""

    def test_no_fix_returns_false(self):
        """C-5: is_applicable returns False when fix is None."""
        d = _diag("SAFE001")

        assert not is_applicable(d, unsafe_fixes=False)
        assert not is_applicable(d, unsafe_fixes=True)

    def test_safe_fix_always_applicable(self):
        """C-6: SAFE fix is applicable regardless of unsafe_fixes flag."""
        d = _diag("SAFE001", Applicability.SAFE)

        assert is_applicable(d, unsafe_fixes=False)
        assert is_applicable(d, unsafe_fixes=True)

    def test_unsafe_fix_requires_flag(self):
        """C-6: UNSAFE fix is only applicable when unsafe_fixes=True."""
        d = _diag("UNSAFE001", Applicability.UNSAFE)

        assert not is_applicable(d, unsafe_fixes=False)
        assert is_applicable(d, unsafe_fixes=True)

    def test_display_only_never_applicable(self):
        """C-6: DISPLAY_ONLY fix is never applicable."""
        d = _diag("SAFE001", Applicability.DISPLAY_ONLY)

        assert not is_applicable(d, unsafe_fixes=False)
        assert not is_applicable(d, unsafe_fixes=True)


class TestRuleRegistry:
    """C-8 to C-11: RuleRegistry."""

    def test_register_and_get(self):
        """C-8: registered rule is retrievable by code."""
        rule = SAFE001(Config())
        registry = make_registry(rule)

        assert registry.get("SAFE001") is rule

    def test_rules_for_kind(self):
        """C-8: rules_for_kind returns rules matching the CST node type."""
        rule = SAFE001(Config())
        registry = make_registry(rule)

        assert rule in registry.rules_for_kind(GoogleDocstring)

    def test_filter_by_codes_ignore(self):
        """C-9: filter_by_codes with ignore removes specified code."""
        registry = make_registry(SAFE001(Config()), UNSAFE001(Config()))

        filtered = registry.filter_by_codes(ignore=frozenset(["SAFE001"]))

        assert filtered.get("SAFE001") is None
        assert filtered.get("UNSAFE001") is not None

    def test_filter_by_codes_select(self):
        """C-10: filter_by_codes with select keeps only specified code."""
        registry = make_registry(SAFE001(Config()), UNSAFE001(Config()))

        filtered = registry.filter_by_codes(select=frozenset(["SAFE001"]))

        assert filtered.get("SAFE001") is not None
        assert filtered.get("UNSAFE001") is None

    def test_filter_by_codes_prefix(self):
        """C-11: prefix in ignore removes all matching codes."""
        registry = make_registry(SAFE001(Config()), UNSAFE001(Config()))

        # "SAFE" prefix matches SAFE001 but not UNSAFE001
        filtered = registry.filter_by_codes(ignore=frozenset(["SAFE"]))

        assert filtered.get("SAFE001") is None
        assert filtered.get("UNSAFE001") is not None
