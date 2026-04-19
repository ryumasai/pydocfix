"""Root-level test configuration and shared utilities."""

from __future__ import annotations

from pydocfix.rules import BaseRule, RuleRegistry


def make_registry(*rule_instances: BaseRule) -> RuleRegistry:
    """Build a RuleRegistry from rule instances."""
    registry = RuleRegistry()
    for rule in rule_instances:
        registry.register(rule)
    return registry


def make_type_to_rules(*rule_instances: BaseRule) -> dict[type, list[BaseRule]]:
    """Build a CST-type-to-rules dispatch map from rule instances."""
    return make_registry(*rule_instances).type_to_rules
