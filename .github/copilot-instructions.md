# Development Guidelines

## Tooling

- Use `uv` as the Python package manager (not pip, poetry, or pipenv)
- Run tests with `uv run pytest` or `python -m pytest tests/`
- Run the linter with `uv run ruff check` / `uv run ruff check --fix`
- Run pydocfix itself with `uv run pydocfix check <path>`

## Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat:     new rule or user-visible feature
fix:      bug fix
refactor: internal restructuring without behaviour change
test:     adding or updating tests
docs:     documentation only
chore:    maintenance (deps, CI, tooling)
```

## Project Structure

```
src/pydocfix/
  rules/
    _base.py          # @rule decorator, context types (FunctionCtx, ClassCtx, ModuleCtx), make_diagnostic
    helpers.py        # shared section-level helpers (find_section, has_section, …)
    <category>/       # one package per rule category (cls, doc, prm, ris, rtn, sum, yld)
      __init__.py     # re-exports rules in the category
      <rule>.py       # one file per rule code (e.g. prm001.py)
  engine/             # checker, registry, fixer, file walker, baseline, noqa
  diagnostics.py      # Diagnostic, Fix, Edit, Applicability, Offset, Range
  config.py           # Config dataclass (loaded from pyproject.toml)
tests/
  rules/<category>/   # snapshot tests per rule
  engine/             # engine-level tests
```

## Key Conventions

- Python ≥ 3.11; use modern syntax (`match`, `X | Y` unions, `list[T]` etc.)
- `from __future__ import annotations` at the top of every source file
- Imports inside rule files must come from `pydocfix.rules._base` and `pydocfix.rules.helpers` directly — never from `pydocfix.rules` (circular import)
- Rules that conflict declare `conflicts_with=frozenset({"OTHER000"})`
- Config-gated rules use `activation_condition=ActivationCondition(attr=..., values=frozenset({...}))`
