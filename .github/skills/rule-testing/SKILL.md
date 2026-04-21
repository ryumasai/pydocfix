---
name: rule-testing
description: Comprehensive skill for testing pydocfix docstring linting rules
---

# Rule Testing

This skill provides support for testing pydocfix docstring linting rules using **ruff-style snapshot testing**.

## Testing Philosophy

Each rule has:
1. **One merged fixture file** (`tests/rules/{category}/fixtures/{rule_code}.py`) containing both violation cases and non-violation cases.
2. **One test file** (`tests/rules/{category}/test_{rule_code}.py`) with snapshot tests.
3. **Snapshots** stored in `tests/rules/{category}/__snapshots__/`.

Snapshots test:
- A **combined output** of diagnostics + fixed source (via `check_rule()`) — one snapshot per rule.

## Fixture Structure

```
tests/rules/{category}/
├── test_{rule_code}.py          # Test code (snapshot-based)
├── __snapshots__/               # Generated snapshots (auto-managed)
│   └── test_{rule_code}.ambr
└── fixtures/
    └── {rule_code}.py           # Single merged fixture (violations + no-violations)
```

### Fixture File Format

```python
# Fixture for {RULE_CODE}: {brief description}.
# Requires Config(...) if non-default config needed.


# violation
def violating_function(...):
    """..."""
    pass


# no violation
def valid_function(...):
    """..."""
    pass
```

No module docstring with metadata — just human-readable comments.

## Test File Pattern

```python
"""Tests for {RULE_CODE}: {description}."""

from __future__ import annotations

from pydocfix.config import Config  # if needed
from pydocfix.rules.{category}.{rule_code} import {RULE_CODE}

from ..conftest import check_rule, load_fixture

CATEGORY = "{category}"


class Test{RULE_CODE}:
    def _rules(self):
        return [{RULE_CODE}()]  # Add Config() args as needed

    def test_rule(self, snapshot):
        fixture = load_fixture("{rule_code}.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="{rule_code}.py") == snapshot
```

- Use `unsafe_fixes=True` if the rule has an UNSAFE fix: `check_rule(..., unsafe_fixes=True)`. The default is already `True`, so this can be omitted in most cases.
- One test method per rule — no separate `test_violations` / `test_fix`.

## Helper Functions (from conftest.py)

```python
# Load the flat fixture file
fixture = load_fixture("prm001.py", "prm")

# Run rule and get combined diagnostics + fixed source (main helper)
output = check_rule(fixture, rules, display_path="prm001.py")
output = check_rule(fixture, rules, display_path="prm001.py", unsafe_fixes=True)  # for UNSAFE fix

# Lower-level helpers (still available)
diag_str = render_fixture(fixture, rules, display_path="prm001.py")  # diagnostics only
fixed_src = fix_fixture(fixture, rules, unsafe_fixes=True)           # fixed source only
```

`check_rule()` output format:
```
━━━ Diagnostics ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRM001 [unsafe] Missing Args/Parameters section in docstring.
  --> prm001.py:7:8
   |
 6 | def missing_args_section(x: int) -> None:
 7 |     """Do something."""
   |        ^^^^^^^^^^^^^
 8 |     pass
   |

━━━ Diff ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--- prm001.py
+++ prm001.py (fixed)
@@ -4,3 +4,7 @@
 def missing_args_section(x: int) -> None:
-    """Do something."""
+    """Do something.
+
+    Args:
+        x: ...
+    """
     pass
```
If no violations: `(none)` under Diagnostics. If no fix: `(no fix)` under Diff.

## Workflow: Creating Tests for a New Rule

1. **Read** `src/pydocfix/rules/{category}/{rule_code}.py` to understand the rule.
2. **Create** `tests/rules/{category}/fixtures/{rule_code}.py` with violation + no-violation cases.
3. **Create** `tests/rules/{category}/test_{rule_code}.py` using the pattern above.
4. **Generate snapshots**: `pytest tests/rules/{category}/test_{rule_code}.py --snapshot-update`
5. **Verify**: `pytest tests/rules/{category}/test_{rule_code}.py`

## Important Notes

- `check_rule()` output always contains both `━━━ Diagnostics ━━━` and `━━━ Diff ━━━` sections. When no violations: `(none)`. When no fix: `(no fix)`.
- For rules requiring non-default config (e.g., `skip_short_docstrings=False`, `type_annotation_style="docstring"`), pass the config in `_rules()`.
- Snapshot files are auto-managed by syrupy. Never edit `.ambr` files manually.
- To regenerate all snapshots: `pytest tests/rules/ --snapshot-update`

## Context Files

- `tests/rules/conftest.py` — Shared helpers (`render_fixture`, `fix_fixture`, `load_fixture`, etc.)
- `tests/rules/{category}/fixtures/{rule_code}.py` — Fixture file
- `tests/rules/{category}/test_{rule_code}.py` — Test file
- `src/pydocfix/rules/{category}/{rule_code}.py` — Rule implementation
- `src/pydocfix/render.py` — `render_diagnostic()` function (ruff-style output)
