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
- **40 rules** across 6 categories: Summary, Parameters, Returns, Yields, Raises, Docstring
- **Google & NumPy style** support (powered by [pydocstring-rs](https://github.com/aita/pydocstring-rs))
- **Signature ↔ docstring consistency** — type mismatches, missing/extra parameters, ordering
- **Default value checking** — detect missing `optional` / `default` annotations
- **Precise diagnostics** — byte-level position information for every violation
- **Baseline** — suppress existing violations so only new ones are reported
- **noqa** — suppress specific violations inline or file-wide

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

## Suppressing violations

### Inline suppression (`# noqa`)

Add a `# noqa` comment on the **closing `"""`** line to suppress violations for that docstring.

```python
def foo(x):
    """Short summary."""  # noqa                    # suppress all rules for this docstring

def bar(x):
    """Short summary."""  # noqa: PRM001            # suppress only PRM001

def baz(x):
    """Short summary."""  # noqa: PRM001, RTN001    # suppress multiple rules

# For multiline docstrings, put the comment on the closing """ line
def qux(x: int) -> int:
    """Short summary.

    Args:
        x: A value.
    """  # noqa: RTN001
    return x
```

Unused `# noqa` codes are reported as **NOQ001** (and removed by `--fix`).

### File-level suppression

Put a `# pydocfix: noqa` comment on its **own line** anywhere in the file to suppress violations for every docstring in the file.

```python
# pydocfix: noqa            # suppress all rules in this file
# pydocfix: noqa: PRM001    # suppress only PRM001 in this file
```

## Baseline

The baseline lets you record the current violation state of a project and suppress those existing violations on future runs — so only *new* violations are reported.
This makes gradual adoption easier: fix violations at your own pace.

```bash
# Record all current violations as the baseline
pydocfix check src/ --baseline .pydocfix-baseline.json --generate-baseline

# Future runs only report violations not in the baseline
pydocfix check src/ --baseline .pydocfix-baseline.json
```

Or configure the baseline path in `pyproject.toml` so you don't need the flag every time:

```toml
[tool.pydocfix]
baseline = ".pydocfix-baseline.json"
```

Then generate and use it:

```bash
pydocfix check src/ --generate-baseline    # write baseline
pydocfix check src/                        # only new violations reported
```

The baseline file is a JSON file that records violations by **symbol name** (e.g. `MyClass.my_method`) rather than line number, so it stays stable when unrelated code is added or removed.
Fixed violations are automatically removed from the baseline on the next run.

## Configuration

Configure via `pyproject.toml`:

```toml
[tool.pydocfix]
# Both accept individual codes (e.g. "PRM001"), category prefixes (e.g. "RIS"), or "ALL"
select = ["ALL"]
ignore = ["PRM001", "RTN001", "YLD001", "RIS"]

# Type annotation style: "signature", "docstring", "both", or omitted (default)
    # - omitted:     PRM104/RTN104/YLD104 and PRM103/RTN103/YLD103 are all disabled (default)
    # - "signature": types live in the function signature; missing signature annotations are flagged (PRM105/RTN105/YLD105),
    #                redundant docstring types are flagged (PRM104/RTN104/YLD104)
    # - "docstring": types live in the docstring; missing docstring types are flagged (PRM103/RTN103/YLD103),
    #                redundant signature annotations are flagged (PRM106/RTN106/YLD106)
    # - "both":      types must appear in both; missing docstring types are flagged (PRM103/RTN103/YLD103),
    #                missing signature annotations are flagged (PRM105/RTN105/YLD105)
type_annotation_style = "signature"

# Paths/patterns to exclude (in addition to built-in defaults)
exclude = ["tests/", "docs/"]

# Skip section-level rules (PRM001, RTN001, YLD001, RIS001) for one-line docstrings (default: true)
skip_short_docstrings = true

# Treat Optional[T], T | None, and Union[T, None] as equivalent to T when
# comparing signature annotations to docstring types in PRM101/RTN101/YLD101 (default: false)
allow_optional_shorthand = false

# Path to the baseline file (relative to pyproject.toml)
baseline = ".pydocfix-baseline.json"
```

## Rules

40 rules across 6 categories. Each rule is classified as **safe** fix, **unsafe** fix, or report-only.

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
| PRM103 | | unsafe | No type in docstring |
| PRM104 | | safe | Redundant type in docstring (signature has annotation) |
| PRM105 | | — | No type annotation in signature (`type_annotation_style = "signature"` or `"both"`) |
| PRM106 | | — | Redundant type annotation in signature (`type_annotation_style = "docstring"`) |
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
| RTN103 | | unsafe | No return type in docstring |
| RTN104 | | safe | Redundant return type in docstring |
| RTN105 | | — | No return type annotation in signature (`type_annotation_style = "signature"` or `"both"`) |
| RTN106 | | — | Redundant return type annotation in signature (`type_annotation_style = "docstring"`) |

### Yields (YLD)

| Code | Default | Fix | Description |
|------|:-------:|:---:|-------------|
| YLD001 | ✅ | unsafe | Missing Yields section |
| YLD002 | ✅ | safe | Unnecessary Yields section |
| YLD003 | ✅ | — | Yields entry has no description |
| YLD101 | ✅ | unsafe | Yield type mismatch |
| YLD102 | ✅ | unsafe | No yield type anywhere |
| YLD103 | | unsafe | No yield type in docstring |
| YLD104 | | safe | Redundant yield type in docstring |
| YLD105 | | — | No yield type annotation in signature (`type_annotation_style = "signature"` or `"both"`) |
| YLD106 | | — | Redundant yield type annotation in signature (`type_annotation_style = "docstring"`) |

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
| [numpy](https://github.com/numpy/numpy) | 425 | 251K | 3.1 sec | 3.0 sec |
| [scikit-learn](https://github.com/scikit-learn/scikit-learn) | 635 | 372K | 3.0 sec | 4.3 sec |

> pydocfix is in early development. The majority of processing time is spent in the Rust-based CST parser (pydocstring-rs); adding more Python-side rules has limited impact on overall throughput.

## License

MIT
