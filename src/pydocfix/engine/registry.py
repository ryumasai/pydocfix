"""Rule registry and applicability logic."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydocfix.diagnostics import Applicability, Diagnostic

if TYPE_CHECKING:
    from pydocfix.config import Config
    from pydocfix.rules._base import RuleFn


def _matches_any(code: str, patterns: frozenset[str]) -> bool:
    """Return True if *code* matches any pattern (exact, prefix, or ``ALL``)."""
    return "ALL" in patterns or any(code == p or code.startswith(p) for p in patterns)


def effective_applicability(diag: Diagnostic, config: Config | None = None) -> Applicability:
    """Return the effective applicability of a diagnostic's fix, after config overrides."""
    if diag.fix is None:
        raise ValueError("effective_applicability() requires a diagnostic with a fix; got fix=None")
    applicability = diag.fix.applicability
    if config is not None:
        code = diag.rule.upper()
        safe_patterns = frozenset(c.upper() for c in config.extend_safe_fixes)
        if safe_patterns and _matches_any(code, safe_patterns):
            return Applicability.SAFE
        unsafe_patterns = frozenset(c.upper() for c in config.extend_unsafe_fixes)
        if unsafe_patterns and _matches_any(code, unsafe_patterns):
            return Applicability.UNSAFE
    return applicability


def is_applicable(diag: Diagnostic, unsafe_fixes: bool, config: Config | None = None) -> bool:
    """Return True if the diagnostic's fix should be applied."""
    if diag.fix is None:
        return False
    app = effective_applicability(diag, config)
    if app == Applicability.SAFE:
        return True
    if app == Applicability.UNSAFE and unsafe_fixes:  # noqa: SIM103
        return True
    return False


@dataclass
class RuleRegistry:
    """Manages available rule functions."""

    _rules: dict[str, RuleFn] = field(default_factory=dict)
    _handlers: dict[tuple[type, type], list[RuleFn]] = field(default_factory=lambda: defaultdict(list))

    def register(self, rule_fn: RuleFn) -> None:
        """Register a rule function (decorated with ``@rule``)."""
        code: str = rule_fn._rule_code  # type: ignore[attr-defined]
        self._rules[code] = rule_fn
        for ctx_type in rule_fn._targets_ctx:  # type: ignore[attr-defined]
            for cst_type in rule_fn._targets_cst:  # type: ignore[attr-defined]
                self._handlers[(ctx_type, cst_type)].append(rule_fn)

    def get(self, code: str) -> RuleFn | None:
        """Get a rule function by code."""
        return self._rules.get(code)

    def handlers_for(self, ctx_type: type, cst_type: type) -> list[RuleFn]:
        """Get all rule functions for a (ctx_type, cst_type) pair."""
        return self._handlers.get((ctx_type, cst_type), [])

    def all_rules(self) -> list[RuleFn]:
        """Get all registered rule functions."""
        return list(self._rules.values())

    def all_codes(self) -> frozenset[str]:
        """Get all registered rule codes."""
        return frozenset(self._rules.keys())

    def filter_by_codes(
        self,
        ignore: frozenset[str] | None = None,
        select: frozenset[str] | None = None,
    ) -> RuleRegistry:
        """Create a new registry filtered by rule codes.

        Args:
            ignore: Rule codes to exclude (supports prefixes).
            select: Rule codes to include (supports prefixes).

        Returns:
            A new RuleRegistry containing only filtered rules.

        """
        ignored = ignore or frozenset()
        selected = select or frozenset()

        filtered = RuleRegistry()
        for rule_fn in self.all_rules():
            code = rule_fn._rule_code  # type: ignore[attr-defined]
            if _matches_any(code, ignored):
                continue
            if selected and not _matches_any(code, selected):
                continue
            filtered.register(rule_fn)

        return filtered
