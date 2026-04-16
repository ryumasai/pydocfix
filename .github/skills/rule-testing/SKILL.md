---
name: rule-testing
description: Comprehensive skill for testing pydocfix docstring linting rules
---

# Rule Testing

This skill provides comprehensive support for testing pydocfix docstring linting rules using **fixture-based testing**.

## Testing Philosophy

**Fixture-first approach**: Each test case uses a real Python file (fixture) in `tests/rules/{category}/fixtures/`. This provides:
- ✅ Realistic, complete Python files
- ✅ Visual verification of rule behavior
- ✅ Easy snapshot testing for auto-fix
- ✅ Clear test intent through file names
- ✅ Reusable test cases

## Fixture Structure

```
tests/rules/{category}/
├── test_{rule_code}.py          # Test code
└── fixtures/
    ├── {rule_code}_no_violation.py
    ├── {rule_code}_violation_basic.py
    └── {rule_code}_violation_complex.py
```

### Fixture File Format

Each fixture file must include a module docstring with metadata:

```python
"""Test fixture for {RULE_CODE}: {description}.

Expected: {N} violation(s) ({RULE_CODE})
Fix: {yes|no|unsafe}
"""

# Actual Python code to test
def example():
    \"\"\"Docstring content.\"\"\"
    pass
```

## Overview

This skill handles three essential test-related tasks:
- **Create**: Generate complete test files with fixture files for all edge cases
- **Verify**: Check test coverage against SKILL.md checklist
- **Snapshot**: Generate snapshot tests for auto-fix functionality

## Task 1: Create Complete Test File

Create a comprehensive test file for a pydocfix rule with all edge cases, including fixture files.

### When to Use
- "Create test for SUM001"
- "Generate test file for PRM001 rule"
- "I need tests for RTN001"
- "@workspace /new Create comprehensive tests for YLD001"

### Instructions

1. **Read specifications:**
   - Read rule specification from `tests/rules/SKILL.md`
   - Read rule implementation from `src/pydocfix/rules/{category}/{rule_code}.py`
   - Identify rule code, category, and whether auto-fix is available

2. **Check existing files:**
   - Check if test file exists at `tests/rules/{category}/test_{rule_code}.py`
   - Check if fixtures directory exists at `tests/rules/{category}/fixtures/`
   - If files exist, ask user if they want to recreate or add to them

3. **Create fixture files** in `tests/rules/{category}/fixtures/`:

   **Required fixtures:**
   - `{rule_code}_violation_basic.py` - Simple violation case
   - `{rule_code}_no_violation.py` - Valid code that should pass

   **Additional fixtures (as needed):**
   - `{rule_code}_violation_complex.py` - Complex case (*args, **kwargs, etc.)
   - `{rule_code}_numpy_style.py` - NumPy-style docstring variant
   - `{rule_code}_async.py` - Async function variant
   - `{rule_code}_multiple.py` - Multiple violations in one file
   - `{rule_code}_edge_empty.py` - Empty docstring edge case

   **Fixture file template:**
   ```python
   """Test fixture for {RULE_CODE}: {brief description}.

   Expected: {N} violation(s) ({RULE_CODE})
   Fix: {yes|no|unsafe}
   """


   def example_function(param: str):
       \"\"\"Docstring content.\"\"\"
       pass
   ```

4. **Create test file** at `tests/rules/{category}/test_{rule_code}.py`:

   **File structure:**
   - File docstring with rule code and description
   - Import statements (pydocfix.rules, conftest helpers)
   - `CATEGORY = "{category}"` constant

   **Main test class `Test{RULE_CODE}`:**
   - `test_violation_basic()` - Load and check basic violation fixture
   - `test_no_violation()` - Load and check no-violation fixture
   - `test_violation_complex()` - Complex case (if relevant)
   - `test_numpy_style()` - NumPy style variant
   - `test_async_function()` - Async function (if relevant)
   - `test_multiple_violations()` - Multiple issues (if relevant)
   - `test_fix_available()` - If auto-fix exists, test it works
   - `test_fix_idempotent()` - If auto-fix exists, applying twice gives same result

   **Snapshot test class `Test{RULE_CODE}Snapshot` (if auto-fix):**
   - `test_fix_basic()` - Basic fix snapshot using fixture
   - `test_fix_complex()` - Complex fix snapshot
   - `test_fix_numpy_style()` - NumPy style fix snapshot

5. **Implementation guidelines:**
   - Use `load_fixture()` and `check_fixture_file()` from conftest.py
   - Follow naming conventions: `{rule_code}_{scenario}.py`
   - Include descriptive docstrings for all test methods
   - Ensure fixture metadata matches actual expectations
   - All edge cases from SKILL.md checklist should have fixtures

6. **Assertions to include:**
   - Number of diagnostics matches fixture metadata
   - Rule code matches expected
   - Fix availability and applicability (SAFE/UNSAFE)
   - For snapshots: fixed content matches expected

## Task 2: Verify Test Coverage

Verify that a test file meets all SKILL.md checklist requirements.

### When to Use
- "Check if SUM001 tests are complete"
- "Verify PRM001 test coverage against SKILL.md"
- "Does test_rtn001.py meet all requirements?"
- "@workspace Analyze test coverage for YLD001"

### Instructions

1. Identify the rule code and test file from the request
2. Read the test file at `tests/rules/{category}/test_{rule_code}.py`
3. List fixture files in `tests/rules/{category}/fixtures/`
4. Read the rule specification from `tests/rules/SKILL.md`
5. Check against the SKILL.md checklist:

   **Basic fixtures:**
   - [ ] `{rule_code}_violation_basic.py` exists
   - [ ] `{rule_code}_no_violation.py` exists
   - [ ] NumPy style fixture exists (if applicable)

   **Basic tests:**
   - [ ] `test_violation_basic` exists and uses fixture
   - [ ] `test_no_violation` exists and uses fixture
   - [ ] Both Google and NumPy styles tested

   **Auto-fix tests (if applicable):**
   - [ ] `test_fix_available` exists
   - [ ] `test_fix_idempotent` exists
   - [ ] Applicability verified (SAFE/UNSAFE)
   - [ ] Fixed content validated

   **Snapshot tests (if auto-fix):**
   - [ ] `Test{RULE_CODE}Snapshot` class exists
   - [ ] `test_fix_basic` snapshot exists using fixture
   - [ ] `test_fix_complex` snapshot exists (if relevant)

   **Edge cases:**
   - [ ] Complex signature fixture (*args, **kwargs)
   - [ ] Async function fixture (where relevant)
   - [ ] Multiple violations fixture (where relevant)

6. Report which checklist items are missing
7. Suggest specific fixtures and test methods to add
8. Provide code snippets for missing test cases
9. Calculate approximate test coverage percentage

## Task 3: Generate Snapshot Test

Generate snapshot tests for rules with auto-fix capability using fixture files.

### When to Use
- "Generate snapshot tests for PRM001"
- "Add snapshot test class to SUM002"
- "Create fix snapshots for RTN001"
- "@workspace Add comprehensive snapshot tests to test_prm004.py"

### Instructions

1. Identify the rule code from the request
2. Check if the rule has auto-fix by reading the rule implementation
3. If no auto-fix, inform user that snapshot tests are not applicable
4. Check if fixture files exist for this rule
5. Read existing test file to see if `Test{RULE_CODE}Snapshot` class exists
6. Create or extend the snapshot test class with these methods:
   - `test_fix_basic()` - Use `{rule_code}_violation_basic.py` fixture
   - `test_fix_complex()` - Use `{rule_code}_violation_complex.py` fixture
   - `test_fix_numpy_style()` - Use NumPy style fixture

7. Each snapshot test should:
   - Load fixture with `load_fixture()`
   - Run `check_fixture_file()` with `fix=True`
   - Assert diagnostic exists with fix
   - Assert `fixed_source == snapshot`

8. Add pytest fixture parameter: `def test_name(self, snapshot):`
9. Include descriptive docstrings explaining scenarios
10. After creation, inform user to run: `pytest {test_file} --snapshot-update`

## Context Files

The following files are essential context for all tasks:

- `tests/rules/SKILL.md` - Test specification, rule details, and checklist
- `tests/rules/conftest.py` - Shared helper functions
- `tests/rules/{category}/test_{rule_code}.py` - Test file (when applicable)
- `tests/rules/{category}/fixtures/` - Fixture files directory
- `src/pydocfix/rules/{category}/{rule_code}.py` - Rule implementation
- `tests/rules/MIGRATION.md` - Migration guide (for context)

## Common Patterns

### Helper Functions (from conftest.py)

**Primary: Fixture-based testing**
```python
# Load a fixture file by name
fixture_path = load_fixture("prm001_violation_basic.py", "prm")

# Check fixture file with rules
diagnostics, fixed_source, original_source = check_fixture_file(
    fixture_path,
    rules=[PRM001()],
    fix=True,
    unsafe_fixes=False,
)
```

**Secondary: String-based testing (for quick inline tests)**
```python
# Create Google-style docstring context
ctx = make_google_context(docstring, func_source, filepath)

# Create NumPy-style docstring context
ctx = make_numpy_context(docstring, func_source, filepath)

# Parse function AST
func = make_function_ast(source)
```

### Fixture-Based Test Structure (Recommended)

```python
"""Tests for {RULE_CODE}: {description}."""

from __future__ import annotations

from pydocfix.rules.{category}.{rule_code} import {RULE_CODE}
from ..conftest import check_fixture_file, load_fixture

CATEGORY = "{category}"


class Test{RULE_CODE}:
    """Test cases for {RULE_CODE}."""

    def test_violation_basic(self):
        """Basic violation case."""
        fixture = load_fixture("{rule_code}_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM001()])

        assert len(diagnostics) == 1
        assert diagnostics[0].code == "{RULE_CODE}"
        assert diagnostics[0].fix is not None  # if auto-fix available

    def test_no_violation(self):
        """Valid code should not trigger violation."""
        fixture = load_fixture("{rule_code}_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [{RULE_CODE}()])

        assert len(diagnostics) == 0

    def test_fix_idempotent(self):
        """Applying fix twice should produce same result."""
        fixture = load_fixture("{rule_code}_violation_basic.py", CATEGORY)

        # First fix
        _, fixed1, _ = check_fixture_file(fixture, [{RULE_CODE}()], fix=True)
        assert fixed1 is not None

        # Second fix (on already fixed code)
        fixture.write_text(fixed1)
        diagnostics2, fixed2, _ = check_fixture_file(fixture, [{RULE_CODE}()])

        assert len(diagnostics2) == 0
        assert fixed2 is None  # No more fixes needed


class Test{RULE_CODE}Snapshot:
    """Snapshot tests for {RULE_CODE} auto-fix."""

    def test_fix_basic(self, snapshot):
        """Basic fix snapshot."""
        fixture = load_fixture("{rule_code}_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [{RULE_CODE}()], fix=True)

        assert fixed is not None
        assert fixed == snapshot

    def test_fix_complex(self, snapshot):
        """Complex case fix snapshot."""
        fixture = load_fixture("{rule_code}_violation_complex.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [{RULE_CODE}()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
```

### String-Based Test Structure (For inline/quick tests)

```python
class Test{RULE_CODE}:
    def test_violation_detected(self):
        """Quick inline test."""
        docstring = '"""Missing something."""'
        func_source = 'def foo(param: str): pass'
        ctx = make_google_context(docstring, func_source)

        rule = {RULE_CODE}()
        diagnostics = list(rule.diagnose(ctx.docstring_cst, ctx))

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "{RULE_CODE}"
```

### Fixture Naming Conventions

| Fixture Type | File Name Pattern | Description |
|--------------|-------------------|-------------|
| Basic violation | `{rule_code}_violation_basic.py` | Simple, minimal violation case |
| No violation | `{rule_code}_no_violation.py` | Valid code that should pass |
| Complex violation | `{rule_code}_violation_complex.py` | *args, **kwargs, defaults, etc. |
| NumPy style | `{rule_code}_numpy_style.py` | NumPy-style docstring variant |
| Async function | `{rule_code}_async.py` | Async function variant |
| Multiple violations | `{rule_code}_multiple.py` | Multiple issues in one file |
| Edge cases | `{rule_code}_edge_{description}.py` | Specific edge cases |

### Important Notes

**Diagnostic Attributes:**
- Use `diagnostic.rule` (not `code`) for rule code
- Use `diagnostic.fix` for auto-fix
- Use `diagnostic.fix.applicability` for SAFE/UNSAFE

**Configuration:**
- PlainDocstring requires `Config(skip_short_docstrings=False)` to be tested
- Pass config when creating rule instance: `PRM001(config)`

**Snapshot Testing:**
- Install syrupy: `pip install syrupy`
- Generate snapshots: `pytest {test_file} --snapshot-update`
- Snapshots are stored in `__snapshots__/` directory

## Tips

### Fixture Management
- **Naming**: Use descriptive fixture names: `{rule_code}_{scenario}.py`
- **Metadata**: Always include expected violations/fixes in fixture docstring
- **Reusability**: One fixture can be used in multiple tests
- **Organization**: Group related fixtures (e.g., all numpy style together)

### Test Design
- **Fixture-first**: Create fixture files before writing test code
- **Visual verification**: Fixture files should be readable and realistic
- **Coverage**: Ensure fixtures cover all edge cases from SKILL.md checklist
- **Snapshot testing**: Use for all auto-fix rules to verify complete output

### Best Practices
- Always read `tests/rules/SKILL.md` first to understand rule specifications
- Use `load_fixture()` and `check_fixture_file()` for fixture-based tests
- Include both Google and NumPy style fixtures for comprehensive coverage
- Add descriptive docstrings to all test methods and fixtures
- For snapshot tests, run with `--snapshot-update` first to generate snapshots
- Check rule implementation to understand auto-fix availability and behavior
- Test edge cases: empty strings, complex signatures, async functions
- Verify AST parent type handling where applicable

### When to Use String-Based Tests
String-based tests (using `make_google_context`) are acceptable for:
- Very simple inline test cases
- Quick prototyping during development
- Tests that don't benefit from full file context
- Unit tests of specific CST node types

**But prefer fixture-based tests for:**
- All main test cases
- Auto-fix validation
- Snapshot testing
- Complex multi-function scenarios
- Real-world usage examples
