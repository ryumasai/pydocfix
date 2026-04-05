# pydocfix

[![PyPI - Version](https://img.shields.io/pypi/v/pydocfix?color=0062A8)](https://pypi.org/project/pydocstring-rs/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydocfix?color=0062A8)](https://devguide.python.org/versions/)

A Python docstring linter that checks **signature ↔ docstring consistency** and **auto-fixes** violations.

> [!WARNING]
> This project is currently under active development (v0.1.0a1).
> APIs and behavior may change without notice.

## Why pydocfix?

Existing signature ↔ docstring consistency checkers (such as pydoclint) can report violations but cannot fix them — leaving all corrections to the developer.

pydocfix is built on [pydocstring-rs](https://github.com/aita/pydocstring-rs), a **CST (Concrete Syntax Tree) parser** for docstrings written in Rust by the same author. CST preserves every token's byte offset, whitespace, and formatting, enabling:

- **Byte-level diagnostics** — point to the exact token (parameter name, type annotation, section header), not just the line
- **Surgical auto-fix** — edits replace precise byte ranges, so fixes never corrupt adjacent content
- **Iterative fix loop** — apply non-overlapping fixes, re-parse, repeat until stable

## Features

- **Auto-fix** — Automatically repair docstring issues with safe/unsafe classification
- **35 rules** across 6 categories: Summary, Parameters, Returns, Yields, Raises, Docstring
- **Google & NumPy style** support (powered by [pydocstring-rs](https://github.com/aita/pydocstring-rs))
- **Signature ↔ docstring consistency** — type mismatches, missing/extra parameters, ordering
- **Default value checking** — detect missing `optional` / `default` annotations
- **Precise diagnostics** — byte-level position information for every violation

## Installation

```bash
pip install pydocfix
```

Requires Python 3.11+.

## Quick Start

```bash
# Check docstrings (report only)
pydocfix check src/

# Show diff of proposed fixes
pydocfix check src/ --diff

# Apply safe fixes
pydocfix check src/ --fix

# Apply safe + unsafe fixes
pydocfix check src/ --fix --unsafe-fixes

# Enable all rules (including non-default)
pydocfix check src/ --select ALL

# Select specific rules
pydocfix check src/ --select PRM,RTN

# Ignore specific rules
pydocfix check src/ --ignore SUM001,PRM008
```

## Configuration

Configure via `pyproject.toml`:

```toml
[tool.pydocfix]
# Rules to enable (overrides defaults); supports category prefixes and "ALL"
select = ["ALL"]

# Rules to disable
ignore = ["PRM001", "RTN001", "YLD001", "RIS001"]

# Type annotation style: "signature" (default) or "docstring"
type_annotation_style = "signature"

# Paths/patterns to exclude (in addition to built-in defaults)
exclude = ["tests/", "docs/"]
```

## Rules

35 rules across 6 categories. Each rule is classified as **safe** fix, **unsafe** fix, or report-only.

- **Safe** fixes can be applied automatically with `--fix` (no risk of changing semantics)
- **Unsafe** fixes require `--fix --unsafe-fixes` (may alter docstring meaning)

### Summary (SUM)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| SUM001 | ✅ | — | Missing summary line |
| SUM002 | ✅ | safe | Summary doesn't end with period |

### Parameters (PRM)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| PRM001 | ✅ | unsafe | Missing Args/Parameters section |
| PRM002 | ✅ | safe | Unnecessary Args/Parameters section |
| PRM003 | ✅ | safe | `self`/`cls` documented in docstring |
| PRM004 | ✅ | unsafe | Parameter in signature missing from docstring |
| PRM005 | ✅ | unsafe | Parameter in docstring not in signature |
| PRM006 | ✅ | unsafe | Parameter order mismatch |
| PRM007 | ✅ | unsafe | Duplicate parameter name |
| PRM008 | ✅ | — | Parameter has no description |
| PRM009 | ✅ | safe | Missing `*`/`**` prefix on `*args`/`**kwargs` |
| PRM101 | ✅ | unsafe | Docstring type doesn't match signature annotation |
| PRM102 | ✅ | unsafe | No type in docstring or signature |
| PRM103 | | safe | Redundant type in docstring (signature has annotation) |
| PRM104 | | unsafe | No type in docstring |
| PRM201 | ✅ | unsafe | Missing `optional` for parameter with default |
| PRM202 | | unsafe | Missing `default` for parameter with default |

### Returns (RTN)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| RTN001 | ✅ | unsafe | Missing Returns section |
| RTN002 | ✅ | safe | Unnecessary Returns section |
| RTN003 | ✅ | — | Returns entry has no description |
| RTN101 | ✅ | unsafe | Return type mismatch |
| RTN102 | ✅ | unsafe | No return type anywhere |
| RTN103 | | safe | Redundant return type in docstring |
| RTN104 | | unsafe | No return type in docstring |

### Yields (YLD)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| YLD001 | ✅ | unsafe | Missing Yields section |
| YLD002 | ✅ | safe | Unnecessary Yields section |
| YLD003 | ✅ | — | Yields entry has no description |
| YLD101 | ✅ | unsafe | Yield type mismatch |
| YLD102 | ✅ | unsafe | No yield type anywhere |
| YLD103 | | safe | Redundant yield type in docstring |
| YLD104 | | unsafe | No yield type in docstring |

### Raises (RIS)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| RIS001 | ✅ | unsafe | Missing Raises section |
| RIS002 | ✅ | safe | Unnecessary Raises section |
| RIS003 | ✅ | — | Raises entry has no description |
| RIS004 | ✅ | unsafe | Raised exception not documented |
| RIS005 | ✅ | unsafe | Documented exception not raised |

### Docstring (DOC)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| DOC001 | ✅ | unsafe | Section order doesn't match convention |

## Benchmark

pydocfix performs linting **and** auto-fix generation in a single pass, yet achieves comparable speed to lint-only tools. Below is a comparison with [pydoclint](https://github.com/jsh9/pydoclint), the closest tool in scope (signature ↔ docstring consistency checking, lint-only):

| Project | Files | Lines | pydocfix | pydoclint |
|---------|------:|------:|---------:|----------:|
| [numpy](https://github.com/numpy/numpy) | 425 | 251K | 4.2 sec | 4.6 sec |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | 635 | 372K | 4.1 sec | 5.3 sec |

> pydocfix is in early development. The majority of processing time is spent in the Rust-based CST parser (pydocstring-rs); adding more Python-side rules has limited impact on overall throughput.

## License

MIT
