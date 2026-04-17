---
name: rule-implementation
description: Comprehensive skill for implementing new pydocfix docstring linting rules
---

# Rule Implementation

This skill covers adding a new linting rule to pydocfix end-to-end.

## File Checklist

For a new rule `XYZ000` in category `xyz`:

| File | Action |
|------|--------|
| `src/pydocfix/rules/xyz/xyz000.py` | **Create** — rule implementation |
| `src/pydocfix/rules/xyz/__init__.py` | **Edit** — add import + `__all__` entry |
| `src/pydocfix/rules/__init__.py` | **Edit** — add import + `__all__` entry |
| `tests/rules/xyz/fixtures/xyz000.py` | **Create** — fixture (violations + no-violations) |
| `tests/rules/xyz/test_xyz000.py` | **Create** — snapshot test |
| `README.md` | **Edit** — add row to the rule table under the appropriate category |

If the category `xyz` is new, also create:
- `src/pydocfix/rules/xyz/__init__.py`
- `tests/rules/xyz/__init__.py`
- `tests/rules/xyz/fixtures/` directory

---

## Rule Implementation Pattern

```python
"""Rule XYZ000 - One-line description."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Edit, Fix

class XYZ000(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """One-line description."""

    code = "XYZ000"

    def diagnose(self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = node
        # ... detect violation ...
        fix = Fix(edits=[...], applicability=Applicability.SAFE)
        yield self._make_diagnostic(ctx, "Message.", fix=fix, target=root)
```

### Generic Type Parameter

`BaseRule[T]` determines which CST node types trigger the rule.
Use a union to match multiple styles:

```python
# Matches Google, NumPy, and Plain docstrings
class XYZ000(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
```

### `_make_diagnostic` signature

```python
self._make_diagnostic(ctx, message, *, fix=None, target)
```

- `target` must be a CST node or token that has a `.range` attribute (used to compute source location).
- Pass `fix=None` for detect-only (non-fixable) rules.

---

## Edit Helpers (from `_base.py`)

```python
from pydocfix.rules._base import replace_token, insert_at, delete_range, Edit

replace_token(token, new_text)      # replace a CST token entirely
insert_at(offset, text)             # insert text at a byte offset (no deletion)
delete_range(start, end)            # delete bytes [start, end)
Edit(start, end, new_text)          # low-level: direct byte-range replacement
```

All offsets are **UTF-8 byte positions** relative to the start of the docstring
content (after the opening triple-quote).

### Section-level helpers (from `_helpers.py`)

```python
from pydocfix.rules._helpers import (
    find_section,        # find a section by kind
    has_section,         # bool check for a section
    delete_section_fix,  # Fix that deletes a whole section
    delete_entry_fix,    # Fix that deletes a single entry within a section
    detect_docstring_style,  # "google" | "numpy" | "plain"
)
from pydocfix.rules._base import detect_section_indent, section_append_edit
```

---

## Applicability

```python
from pydocfix.rules._base import Applicability

Applicability.SAFE         # always applied with --fix
Applicability.UNSAFE       # requires --unsafe-fixes
Applicability.DISPLAY_ONLY # shown as suggestion, never applied automatically
```

Guidelines:
- **SAFE** — purely mechanical, no information loss (e.g. reformat whitespace, add period)
- **UNSAFE** — may lose information or change semantics (e.g. delete a section, add stubs)
- **DISPLAY_ONLY** — structural changes that need human review

---

## DiagnoseContext

Available inside `diagnose()` as `ctx`:

```python
ctx.filepath           # Path — source file being checked
ctx.docstring_text     # str  — raw docstring content (without outer quotes)
ctx.docstring_cst      # GoogleDocstring | NumPyDocstring | PlainDocstring
ctx.parent_ast         # ast.AST — function/class/module that owns the docstring
ctx.docstring_stmt     # ast.stmt — the Expr node for the docstring
ctx.docstring_location # DocstringLocation — positional metadata
ctx.cst_node_range(node)  # → Range — convert CST node to file-level Range
```

Useful attributes on `ctx.docstring_location`:
```python
ctx.docstring_location.opening_quote  # e.g. '"""' or "'''"
ctx.docstring_location.content_start  # Offset(lineno, col) of first content char
```

---

## Registering the Rule

### 1. `src/pydocfix/rules/xyz/__init__.py`

```python
"""XYZ-category rules."""

from pydocfix.rules.xyz.xyz000 import XYZ000

__all__ = ["XYZ000"]
```

### 2. `src/pydocfix/rules/__init__.py`

Add an import in the appropriate category block:

```python
# --- XYZ rules ---
from pydocfix.rules.xyz.xyz000 import XYZ000
```

And add to `__all__`:

```python
# xyz
"XYZ000",
```

### 3. `README.md`

Add a row to the rule table under the matching category section (e.g. `### Docstring (DOC)`):

```markdown
| XYZ000 | ✅ | safe | One-line description |
```

Column values:
- **Code** — rule code
- **Default** — `✅` if `enabled_by_default = True`, blank otherwise
- **Fix** — `safe`, `unsafe`, or `—` (no fix)
- **Description** — short human-readable description

---

## Writing Tests

See the [rule-testing skill](./../rule-testing/SKILL.md) for creating tests.

---

## Real Examples to Reference

| Rule | Noteworthy aspect |
|------|------------------|
| `src/pydocfix/rules/sum/sum002.py` | Simple SAFE fix (insert text) |
| `src/pydocfix/rules/doc/doc001.py` | Reorder sections with edits |
| `src/pydocfix/rules/prm/prm002.py` | Delete section (SAFE) |
| `src/pydocfix/rules/prm/prm001.py` | Append new section (UNSAFE) |

---

## Common Pitfalls

- **Do not import from `pydocfix.rules`** inside a rule file — import directly from `pydocfix.rules._base` and `pydocfix.rules._helpers` to avoid circular imports.
- `Edit` offsets are **byte** positions, not character positions. Use `.encode("utf-8")` when computing offsets manually.
- `_make_diagnostic`'s `target` must expose `.range.start` / `.range.end` as integer byte offsets (all CST nodes from pydocstring-rs do).
- When the rule only applies to one docstring style, narrow the generic type: `BaseRule[GoogleDocstring]`.
- Rules that conflict with each other declare `conflicts_with = frozenset({"OTHER000"})`.
- Rules gated on config use `activation_condition = ActivationCondition(attr="type_annotation_style", values=frozenset({"docstring"}))`.
