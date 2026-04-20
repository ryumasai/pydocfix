"""Root-level test configuration and shared utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydocfix.rules import RuleRegistry

if TYPE_CHECKING:
    from pydocfix.rules._base import RuleFn


def make_registry(*rule_fns: RuleFn) -> RuleRegistry:
    """Build a RuleRegistry from rule functions."""
    registry = RuleRegistry()
    for rule_fn in rule_fns:
        registry.register(rule_fn)
    return registry
