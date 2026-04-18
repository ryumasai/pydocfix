"""Rule registry and applicability logic."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydocfix._types import Applicability, Diagnostic

if TYPE_CHECKING:
    from pydocfix.config import Config
    from pydocfix.rules._base import BaseRule


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
    """Manages available rules."""

    _rules: dict[str, BaseRule] = field(default_factory=dict)
    _by_kind: dict[type, list[BaseRule]] = field(default_factory=lambda: defaultdict(list))

    def register(self, rule: BaseRule) -> None:
        """Register a rule instance."""
        self._rules[rule.code] = rule
        for kind in rule._targets:
            self._by_kind[kind].append(rule)

    def get(self, code: str) -> BaseRule | None:
        """Get a rule by code."""
        return self._rules.get(code)

    def rules_for_kind(self, kind: type) -> list[BaseRule]:
        """Get all rules that handle a specific CST node type."""
        return self._by_kind.get(kind, [])

    def all_rules(self) -> list[BaseRule]:
        """Get all registered rules."""
        return list(self._rules.values())

    def all_codes(self) -> frozenset[str]:
        """Get all registered rule codes."""
        return frozenset(self._rules.keys())

    @property
    def type_to_rules(self) -> dict[type, list[BaseRule]]:
        """Get the CST node type to rules mapping."""
        return dict(self._by_kind)

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
        for rule in self.all_rules():
            if _matches_any(rule.code, ignored):
                continue
            if selected and not _matches_any(rule.code, selected):
                continue
            filtered.register(rule)

        return filtered
