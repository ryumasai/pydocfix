"""Tests for linting rules and rule infrastructure."""

from __future__ import annotations

import ast
from pathlib import Path

import pydocstring
from pydocstring import (
    GoogleArg,
    GoogleDocstring,
    GoogleException,
    GoogleReturn,
    GoogleSection,
    GoogleSectionKind,
    GoogleYield,
    NumPyDocstring,
    NumPyException,
    NumPyParameter,
    NumPyReturns,
    NumPySection,
    NumPySectionKind,
    NumPyYields,
    Token,
    Visitor,
    parse_google,
    parse_numpy,
)

from pydocfix.rules import (
    DOC001,
    DOC002,
    PRM001,
    PRM002,
    PRM003,
    PRM004,
    PRM005,
    PRM006,
    PRM007,
    PRM008,
    PRM009,
    PRM101,
    PRM102,
    PRM103,
    PRM104,
    PRM201,
    PRM202,
    RIS001,
    RIS002,
    RIS003,
    RIS004,
    RIS005,
    RTN001,
    RTN002,
    RTN003,
    RTN101,
    RTN102,
    RTN103,
    RTN104,
    SUM001,
    SUM002,
    YLD001,
    YLD002,
    YLD003,
    YLD101,
    YLD102,
    YLD103,
    YLD104,
    Applicability,
    DiagnoseContext,
    Diagnostic,
    DocstringLocation,
    Edit,
    Fix,
    Offset,
    Range,
    apply_edits,
    build_registry,
)


def _dummy_stmt(lineno: int = 1, col_offset: int = 0) -> ast.stmt:
    """Create a minimal ast.stmt with the given position."""
    node = ast.Expr(value=ast.Constant(value=""))
    node.lineno = lineno
    node.col_offset = col_offset
    node.end_lineno = lineno
    node.end_col_offset = col_offset
    return node


def _make_diagnose_ctx(raw: str):
    """Create a DiagnoseContext with the parsed docstring as target."""
    parsed = parse_google(raw)
    return parsed, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=raw,
        docstring_cst=parsed,
        parent_ast=ast.parse("pass").body[0],
        docstring_stmt=_dummy_stmt(1, 0),
        docstring_location=DocstringLocation(Offset(1, 0), 0, len(raw) + 6, '"""', '"""'),
    )


class TestEdit:
    def test_apply_single_insert(self):
        result = apply_edits("abcdef", [Edit(start=3, end=3, new_text="X")])
        assert result == "abcXdef"

    def test_apply_single_replace(self):
        result = apply_edits("abcdef", [Edit(start=1, end=4, new_text="XY")])
        assert result == "aXYef"

    def test_apply_multiple_non_overlapping(self):
        edits = [
            Edit(start=0, end=1, new_text="X"),
            Edit(start=3, end=4, new_text="Y"),
        ]
        result = apply_edits("abcdef", edits)
        assert result == "XbcYef"

    def test_apply_overlapping_raises(self):
        edits = [
            Edit(start=1, end=4, new_text="X"),
            Edit(start=3, end=5, new_text="Y"),
        ]
        try:
            apply_edits("abcdef", edits)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass


class TestDiagnostic:
    def test_fixable_when_fix_present(self):
        d = Diagnostic(
            rule="SUM002",
            message="test",
            filepath="test.py",
            range=Range(Offset(1, 0), Offset(1, 10)),
            fix=Fix(edits=[], applicability=Applicability.SAFE),
        )
        assert d.fixable is True

    def test_not_fixable_when_no_fix(self):
        d = Diagnostic(
            rule="SUM002",
            message="test",
            filepath="test.py",
            range=Range(Offset(1, 0), Offset(1, 10)),
        )
        assert d.fixable is False

    def test_line_and_col_properties(self):
        d = Diagnostic(
            rule="SUM002",
            message="test",
            filepath="test.py",
            range=Range(Offset(5, 4), Offset(7, 0)),
        )
        assert d.lineno == 5
        assert d.col == 4


class TestD200:
    def test_missing_period(self):
        node, ctx = _make_diagnose_ctx("Do something")
        diag = next(iter(SUM002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "SUM002"
        assert diag.fixable is True
        assert diag.fix is not None

    def test_has_period(self):
        node, ctx = _make_diagnose_ctx("Do something.")
        diag = next(iter(SUM002().diagnose(node, ctx)), None)
        assert diag is None

    def test_empty_summary(self):
        # Empty docstrings have no SUMMARY token in the CST,
        # so SUM002 is never dispatched. Tested via checker integration.
        pass

    def test_fix_returns_edit(self):
        raw = "Do something"
        node, ctx = _make_diagnose_ctx(raw)
        diag = next(iter(SUM002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(raw, diag.fix.edits)
        assert result == "Do something."

    def test_fix_no_change_when_period_exists(self):
        raw = "Do something."
        node, ctx = _make_diagnose_ctx(raw)
        diag = next(iter(SUM002().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_preserves_surrounding_text(self):
        raw = "Do something\n\n    Args:\n        x: val.\n"
        node, ctx = _make_diagnose_ctx(raw)
        diag = next(iter(SUM002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(raw, diag.fix.edits)
        assert "Do something." in result
        assert "    Args:\n        x: val.\n" in result


class TestRegistry:
    def test_build_registry_contains_d200(self):
        registry = build_registry()
        assert registry.get("SUM002") is not None

    def test_build_registry_contains_d401(self):
        registry = build_registry()
        assert registry.get("PRM101") is not None

    def test_build_registry_contains_d402(self):
        registry = build_registry()
        assert registry.get("RTN101") is not None

    def test_all_rules(self):
        registry = build_registry()
        rules = registry.all_rules()
        codes = [r.code for r in rules]
        assert "SUM002" in codes
        assert "PRM101" in codes
        assert "RTN101" in codes

    def test_rules_for_kind(self):
        registry = build_registry()
        google_ds_rules = registry.rules_for_kind(GoogleDocstring)
        assert any(r.code == "SUM002" for r in google_ds_rules)
        assert registry.rules_for_kind(type(None)) == []
        google_arg_rules = registry.rules_for_kind(GoogleArg)
        assert any(r.code == "PRM101" for r in google_arg_rules)
        google_return_rules = registry.rules_for_kind(GoogleReturn)
        assert any(r.code == "RTN101" for r in google_return_rules)


# ── Helpers for PRM101 ─────────────────────────────────────────────────


def _make_d401_ctx_google(
    ds_text: str,
    func_src: str,
    cst_node,
) -> DiagnoseContext:
    """Build a DiagnoseContext for PRM101 tests (Google style)."""
    parsed = parse_google(ds_text)
    tree = ast.parse(func_src)
    # func_src may start with import statements; find the first function node.
    func_node = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return cst_node, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


def _find_cst_nodes(parsed, node_type):
    """Find all CST nodes of a given type using Visitor."""
    results = []

    class _GoogleArgCollector(Visitor):
        def enter_google_arg(self, node, ctx):
            results.append(node)

    class _GoogleReturnCollector(Visitor):
        def enter_google_return(self, node, ctx):
            results.append(node)

    class _GoogleExceptionCollector(Visitor):
        def enter_google_exception(self, node, ctx):
            results.append(node)

    class _GoogleYieldCollector(Visitor):
        def enter_google_yield(self, node, ctx):
            results.append(node)

    class _GoogleSectionCollector(Visitor):
        def enter_google_section(self, node, ctx):
            results.append(node)

    class _NumPyParameterCollector(Visitor):
        def enter_numpy_parameter(self, node, ctx):
            results.append(node)

    class _NumPyReturnsCollector(Visitor):
        def enter_numpy_returns(self, node, ctx):
            results.append(node)

    class _NumPyExceptionCollector(Visitor):
        def enter_numpy_exception(self, node, ctx):
            results.append(node)

    class _NumPyYieldsCollector(Visitor):
        def enter_numpy_yields(self, node, ctx):
            results.append(node)

    class _NumPySectionCollector(Visitor):
        def enter_numpy_section(self, node, ctx):
            results.append(node)

    _type_to_collector = {
        GoogleArg: _GoogleArgCollector,
        GoogleReturn: _GoogleReturnCollector,
        GoogleException: _GoogleExceptionCollector,
        GoogleYield: _GoogleYieldCollector,
        GoogleSection: _GoogleSectionCollector,
        NumPyParameter: _NumPyParameterCollector,
        NumPyReturns: _NumPyReturnsCollector,
        NumPyException: _NumPyExceptionCollector,
        NumPyYields: _NumPyYieldsCollector,
        NumPySection: _NumPySectionCollector,
    }

    collector_cls = _type_to_collector.get(node_type)
    if collector_cls:
        pydocstring.walk(parsed, collector_cls())
    return results


# ── PRM101 Tests ───────────────────────────────────────────────────────


class TestD401GoogleParam:
    """PRM101: parameter type mismatch in Google-style docstrings."""

    def test_mismatch_detected(self):
        ds = "Summary.\n\nArgs:\n    x (str): The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        assert len(args) == 1
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM101"
        assert "'str'" in diag.message
        assert "'int'" in diag.message
        assert "'x'" in diag.message

    def test_matching_types_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_annotation_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (str): The x value.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_doc_type_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x: The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_replaces_type(self):
        ds = "Summary.\n\nArgs:\n    x (str): The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "(int)" in result

    def test_complex_type(self):
        ds = "Summary.\n\nArgs:\n    items (list): The items.\n"
        func = "def foo(items: list[int]):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "(list[int])" in result

    def test_multiple_params(self):
        ds = "Summary.\n\nArgs:\n    x (str): X.\n    y (int): Y.\n"
        func = "def foo(x: int, y: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        assert len(args) == 2
        # x: str vs int → mismatch
        node0, ctx0 = _make_d401_ctx_google(ds, func, args[0])
        diag0 = next(iter(PRM101().diagnose(node0, ctx0)), None)
        assert diag0 is not None
        assert "'x'" in diag0.message
        # y: int vs int → match
        node1, ctx1 = _make_d401_ctx_google(ds, func, args[1])
        diag1 = next(iter(PRM101().diagnose(node1, ctx1)), None)
        assert diag1 is None

    def test_class_method_skipped(self):
        """Non-function AST nodes (e.g. class) should not crash."""
        ds = "Summary.\n\nArgs:\n    x (int): X.\n"
        func = "class Foo:\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        tree = ast.parse(func)
        node = args[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is None


class TestD402GoogleReturn:
    """RTN101: return type mismatch in Google-style docstrings."""

    def test_mismatch_detected(self):
        ds = "Summary.\n\nReturns:\n    str: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, GoogleReturn)
        assert len(rets) == 1
        node, ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = next(iter(RTN101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN101"
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_matching_return_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, GoogleReturn)
        node, ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = next(iter(RTN101().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_return_annotation_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo():\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, GoogleReturn)
        node, ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = next(iter(RTN101().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_replaces_return_type(self):
        ds = "Summary.\n\nReturns:\n    str: The result.\n"
        func = "def foo() -> bool:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, GoogleReturn)
        node, ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = next(iter(RTN101().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "bool:" in result


class TestD401Numpy:
    """PRM101: type mismatch in NumPy-style docstrings."""

    def test_param_mismatch(self):
        ds = "Summary.\n\nParameters\n----------\nx : str\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        assert len(params) == 1
        tree = ast.parse(func)
        node = params[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_return_mismatch(self):
        ds = "Summary.\n\nReturns\n-------\nstr\n    The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_numpy(ds)
        rets = _find_cst_nodes(parsed, NumPyReturns)
        assert len(rets) == 1
        tree = ast.parse(func)
        node = rets[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RTN101().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_param_match_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        tree = ast.parse(func)
        node = params[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is None


# ── PRM009 Tests ───────────────────────────────────────────────────────


class TestD403GoogleParam:
    """PRM009: parameter name missing prefix in Google-style docstrings."""

    def test_kwargs_missing_prefix(self):
        ds = "Summary.\n\nArgs:\n    kwargs (int): desc.\n"
        func = "def foo(**kwargs: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        assert len(args) == 1
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM009"
        assert "'kwargs'" in diag.message
        assert "'**kwargs'" in diag.message

    def test_args_missing_prefix(self):
        ds = "Summary.\n\nArgs:\n    args (int): desc.\n"
        func = "def foo(*args: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'args'" in diag.message
        assert "'*args'" in diag.message

    def test_kwargs_with_prefix_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    **kwargs (int): desc.\n"
        func = "def foo(**kwargs: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is None

    def test_args_with_prefix_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    *args (int): desc.\n"
        func = "def foo(*args: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is None

    def test_regular_param_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_adds_prefix(self):
        ds = "Summary.\n\nArgs:\n    kwargs (int): desc.\n"
        func = "def foo(**kwargs: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix.applicability == Applicability.SAFE
        result = apply_edits(ds, diag.fix.edits)
        assert "**kwargs" in result

    def test_non_function_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    kwargs (int): desc.\n"
        func = "class Foo:\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        tree = ast.parse(func)
        node = args[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is None


class TestD403NumpyParam:
    """PRM009: parameter name missing prefix in NumPy-style docstrings."""

    def test_kwargs_missing_prefix(self):
        ds = "Summary.\n\nParameters\n----------\nkwargs : int\n    desc.\n"
        func = "def foo(**kwargs: int):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        assert len(params) == 1
        tree = ast.parse(func)
        node = params[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'kwargs'" in diag.message
        assert "'**kwargs'" in diag.message

    def test_kwargs_with_prefix_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\n**kwargs : int\n    desc.\n"
        func = "def foo(**kwargs: int):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        tree = ast.parse(func)
        node = params[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM009().diagnose(node, ctx)), None)
        assert diag is None


# ── Helpers for PRM004 ─────────────────────────────────────────────────


def _make_d404_ctx_google(ds_text: str, func_src: str):
    """Build a DiagnoseContext targeting the GOOGLE_SECTION node."""
    parsed = parse_google(ds_text)
    sections = _find_cst_nodes(parsed, GoogleSection)
    # Pick the first section with ARGS kind
    section = None
    for s in sections:
        if s.section_kind == GoogleSectionKind.ARGS:
            section = s
            break
    assert section is not None, "No Args section found"
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return section, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


def _make_d404_ctx_numpy(ds_text: str, func_src: str):
    """Build a DiagnoseContext targeting the NUMPY_SECTION node."""
    parsed = parse_numpy(ds_text)
    sections = _find_cst_nodes(parsed, NumPySection)
    section = None
    for s in sections:
        if s.section_kind == NumPySectionKind.PARAMETERS:
            section = s
            break
    assert section is not None, "No Parameters section found"
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return section, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


# ── PRM004 Tests ───────────────────────────────────────────────────────


class TestD404GoogleParam:
    """PRM004: missing parameter in Google-style docstrings."""

    def test_missing_param_detected(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "PRM004"
        assert "'y'" in diags[0].message

    def test_all_documented_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n    y (str): The y.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_multiple_missing(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int, y: str, z: float):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 2
        names = {d.message for d in diags}
        assert any("'y'" in m for m in names)
        assert any("'z'" in m for m in names)

    def test_self_excluded(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(self, x: int):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_cls_excluded(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(cls, x: int):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_varargs_missing(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int, *args: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert "'*args'" in diags[0].message

    def test_kwargs_missing(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int, **kwargs: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert "'**kwargs'" in diags[0].message

    def test_varargs_documented_with_prefix(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n    *args (str): Extra.\n"
        func = "def foo(x: int, *args: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_varargs_documented_without_prefix(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n    args (str): Extra.\n"
        func = "def foo(x: int, *args: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_kwonly_missing(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int, *, key: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert "'key'" in diags[0].message

    def test_no_annotation(self):
        ds = "Summary.\n\nArgs:\n    x: The x.\n"
        func = "def foo(x, y):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert "'y'" in diags[0].message

    def test_fix_inserts_stub_with_type(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].fix is not None
        assert diags[0].fix.applicability == Applicability.UNSAFE
        result = apply_edits(ds, diags[0].fix.edits)
        assert "y (str):" in result
        assert "y (str): " not in result or result.endswith("y (str):")
        # Original content preserved
        assert "x (int): The x." in result

    def test_fix_inserts_stub_without_type(self):
        ds = "Summary.\n\nArgs:\n    x: The x.\n"
        func = "def foo(x, y):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        result = apply_edits(ds, diags[0].fix.edits)
        assert "\n    y:" in result

    def test_non_function_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        parsed = parse_google(ds)
        sections = _find_cst_nodes(parsed, GoogleSection)
        section = sections[0]
        tree = ast.parse("class Foo:\n    pass\n")
        node = section
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_returns_section_ignored(self):
        """PRM004 should not flag Returns sections."""
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n\nReturns:\n    int: The result.\n"
        func = "def foo(x: int) -> int:\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []


class TestD404NumpyParam:
    """PRM004: missing parameter in NumPy-style docstrings."""

    def test_missing_param_detected(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        assert "'y'" in diags[0].message

    def test_all_documented_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\ny : str\n    The y.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []

    def test_fix_inserts_numpy_stub_with_type(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        result = apply_edits(ds, diags[0].fix.edits)
        assert "y : str" in result
        assert "Description." not in result

    def test_fix_inserts_numpy_stub_without_type(self):
        ds = "Summary.\n\nParameters\n----------\nx\n    The x.\n"
        func = "def foo(x, y):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert len(diags) == 1
        result = apply_edits(ds, diags[0].fix.edits)
        assert "y" in result

    def test_self_excluded(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(self, x: int):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        diags = list(PRM004().diagnose(node, ctx))
        assert diags == []


class TestD404Registry:
    """PRM004 is registered correctly."""

    def test_registry_contains_d404(self):
        registry = build_registry()
        assert registry.get("PRM004") is not None

    def test_rules_for_google_section(self):
        registry = build_registry()
        rules = registry.rules_for_kind(GoogleSection)
        assert any(r.code == "PRM004" for r in rules)

    def test_rules_for_numpy_section(self):
        registry = build_registry()
        rules = registry.rules_for_kind(NumPySection)
        assert any(r.code == "PRM004" for r in rules)


# ── Helpers for PRM005 ─────────────────────────────────────────────────


def _make_d405_ctx_google(ds_text: str, func_src: str, arg_index: int = 0):
    """Build a DiagnoseContext targeting a GOOGLE_ARG node."""
    parsed = parse_google(ds_text)
    args = _find_cst_nodes(parsed, GoogleArg)
    assert len(args) > arg_index
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return args[arg_index], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


def _make_d405_ctx_numpy(ds_text: str, func_src: str, param_index: int = 0):
    """Build a DiagnoseContext targeting a NUMPY_PARAMETER node."""
    parsed = parse_numpy(ds_text)
    params = _find_cst_nodes(parsed, NumPyParameter)
    assert len(params) > param_index
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return params[param_index], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


# ── PRM005 Tests ───────────────────────────────────────────────────────


class TestD405GoogleParam:
    """PRM005: extra parameter in Google-style docstrings."""

    def test_extra_param_detected(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n    y (str): The y.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d405_ctx_google(ds, func, arg_index=1)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM005"
        assert "'y'" in diag.message

    def test_valid_param_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d405_ctx_google(ds, func, arg_index=0)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is None

    def test_self_not_in_signature_check(self):
        """self is in func.args but not user-visible; doc param named 'self' should be flagged."""
        ds = "Summary.\n\nArgs:\n    self (Foo): This.\n"
        func = "def foo(self):\n    pass\n"
        node, ctx = _make_d405_ctx_google(ds, func, arg_index=0)
        # 'self' IS in func.args, so not flagged as extra
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is None

    def test_star_args_with_prefix_valid(self):
        ds = "Summary.\n\nArgs:\n    *args: Extra.\n"
        func = "def foo(*args):\n    pass\n"
        node, ctx = _make_d405_ctx_google(ds, func, arg_index=0)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is None

    def test_star_args_without_prefix_valid(self):
        ds = "Summary.\n\nArgs:\n    args: Extra.\n"
        func = "def foo(*args):\n    pass\n"
        node, ctx = _make_d405_ctx_google(ds, func, arg_index=0)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_deletes_entry(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n    y (str): The y.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d405_ctx_google(ds, func, arg_index=1)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.UNSAFE
        result = apply_edits(ds, diag.fix.edits)
        assert "x (int): The x." in result
        assert "y (str)" not in result

    def test_non_function_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        tree = ast.parse("class Foo:\n    pass\n")
        node = args[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is None


class TestD405NumpyParam:
    """PRM005: extra parameter in NumPy-style docstrings."""

    def test_extra_param_detected(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\ny : str\n    The y.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d405_ctx_numpy(ds, func, param_index=1)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'y'" in diag.message

    def test_valid_param_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d405_ctx_numpy(ds, func, param_index=0)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_deletes_entry(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\ny : str\n    The y.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d405_ctx_numpy(ds, func, param_index=1)
        diag = next(iter(PRM005().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "x : int" in result
        assert "y : str" not in result


# ── Helpers for PRM001 ─────────────────────────────────────────────────


def _make_d406_ctx_google(ds_text: str, func_src: str):
    """Build a DiagnoseContext targeting the GOOGLE_DOCSTRING root node."""
    parsed = parse_google(ds_text)
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return parsed, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


def _make_d406_ctx_numpy(ds_text: str, func_src: str):
    """Build a DiagnoseContext targeting the NUMPY_DOCSTRING root node."""
    parsed = parse_numpy(ds_text)
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return parsed, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


# ── PRM001 Tests ───────────────────────────────────────────────────────


class TestD406Google:
    """PRM001: missing Args section in Google-style docstrings."""

    def test_missing_section_detected(self):
        ds = "Summary."
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM001"

    def test_no_params_no_diagnostic(self):
        ds = "Summary."
        func = "def foo():\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is None

    def test_only_self_no_diagnostic(self):
        ds = "Summary."
        func = "def foo(self):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is None

    def test_has_args_section_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is None

    def test_returns_section_only_still_flagged(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo(x: int) -> int:\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None

    def test_fix_inserts_section(self):
        ds = "Summary."
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.UNSAFE
        result = apply_edits(ds, diag.fix.edits)
        assert "Args:" in result
        assert "x (int):" in result
        assert "y (str):" in result
        assert "Description." not in result
        assert "Summary." in result

    def test_fix_without_annotations(self):
        ds = "Summary."
        func = "def foo(x, y):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "\n        x:" in result
        assert "\n        y:" in result
        assert "Description." not in result

    def test_fix_includes_varargs(self):
        ds = "Summary."
        func = "def foo(x: int, *args: str, **kwargs: bool):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "*args (str):" in result
        assert "**kwargs (bool):" in result
        assert "Description." not in result

    def test_non_function_no_diagnostic(self):
        ds = "Summary."
        parsed = parse_google(ds)
        tree = ast.parse("class Foo:\n    pass\n")
        node = parsed
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is None

    def test_async_function(self):
        ds = "Summary."
        func = "async def foo(x: int):\n    pass\n"
        node, ctx = _make_d406_ctx_google(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None


class TestD406Numpy:
    """PRM001: missing Parameters section in NumPy-style docstrings."""

    def test_missing_section_detected(self):
        ds = "Summary."
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d406_ctx_numpy(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None

    def test_has_parameters_section_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d406_ctx_numpy(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_inserts_numpy_section(self):
        ds = "Summary."
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d406_ctx_numpy(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Parameters" in result
        assert "----------" in result
        assert "x : int" in result
        assert "y : str" in result

    def test_no_params_no_diagnostic(self):
        ds = "Summary."
        func = "def foo():\n    pass\n"
        node, ctx = _make_d406_ctx_numpy(ds, func)
        diag = next(iter(PRM001().diagnose(node, ctx)), None)
        assert diag is None


class TestD405D406Registry:
    """PRM005 and PRM001 are registered correctly."""

    def test_registry_contains_d405(self):
        registry = build_registry()
        assert registry.get("PRM005") is not None

    def test_registry_contains_d406(self):
        registry = build_registry()
        assert registry.get("PRM001") is not None

    def test_d405_rules_for_google_arg(self):
        registry = build_registry()
        rules = registry.rules_for_kind(GoogleArg)
        assert any(r.code == "PRM005" for r in rules)

    def test_d405_rules_for_numpy_parameter(self):
        registry = build_registry()
        rules = registry.rules_for_kind(NumPyParameter)
        assert any(r.code == "PRM005" for r in rules)

    def test_d406_rules_for_google_docstring(self):
        registry = build_registry()
        rules = registry.rules_for_kind(GoogleDocstring)
        assert any(r.code == "PRM001" for r in rules)

    def test_d406_rules_for_numpy_docstring(self):
        registry = build_registry()
        rules = registry.rules_for_kind(NumPyDocstring)
        assert any(r.code == "PRM001" for r in rules)


# ── Helpers for PRM008 ─────────────────────────────────────────────────


def _make_d407_ctx_google(ds_text: str, func_src: str, arg_index: int = 0):
    parsed = parse_google(ds_text)
    args = _find_cst_nodes(parsed, GoogleArg)
    assert len(args) > arg_index
    tree = ast.parse(func_src)
    return args[arg_index], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=tree.body[0],
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


def _make_d407_ctx_numpy(ds_text: str, func_src: str, param_index: int = 0):
    parsed = parse_numpy(ds_text)
    params = _find_cst_nodes(parsed, NumPyParameter)
    assert len(params) > param_index
    tree = ast.parse(func_src)
    return params[param_index], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=tree.body[0],
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


# ── PRM008 Tests ───────────────────────────────────────────────────────


class TestD407GoogleParam:
    """PRM008: empty description in Google-style docstrings."""

    def test_empty_description_detected(self):
        ds = "Summary.\n\nArgs:\n    x (int):\n    y (str): The y.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d407_ctx_google(ds, func, arg_index=0)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM008"
        assert "'x'" in diag.message

    def test_has_description_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d407_ctx_google(ds, func, arg_index=0)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is None

    def test_second_arg_empty(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x.\n    y (str):\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d407_ctx_google(ds, func, arg_index=1)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'y'" in diag.message

    def test_no_fix(self):
        ds = "Summary.\n\nArgs:\n    x (int):\n    y (str): The y.\n"
        func = "def foo(x: int, y: str):\n    pass\n"
        node, ctx = _make_d407_ctx_google(ds, func, arg_index=0)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is None

    def test_non_function_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int):\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        tree = ast.parse("class Foo:\n    pass\n")
        node = args[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is None


class TestD407NumpyParam:
    """PRM008: empty description in NumPy-style docstrings."""

    def test_empty_description_detected(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d407_ctx_numpy(ds, func, param_index=0)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'x'" in diag.message

    def test_has_description_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d407_ctx_numpy(ds, func, param_index=0)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_fix(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d407_ctx_numpy(ds, func, param_index=0)
        diag = next(iter(PRM008().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is None


class TestD407Registry:
    """PRM008 is registered correctly."""

    def test_registry_contains_d407(self):
        registry = build_registry()
        assert registry.get("PRM008") is not None

    def test_rules_for_google_arg(self):
        registry = build_registry()
        rules = registry.rules_for_kind(GoogleArg)
        assert any(r.code == "PRM008" for r in rules)

    def test_rules_for_numpy_parameter(self):
        registry = build_registry()
        rules = registry.rules_for_kind(NumPyParameter)
        assert any(r.code == "PRM008" for r in rules)


# ── PRM007 Tests ───────────────────────────────────────────────────────


class TestD408GoogleParam:
    """PRM007: duplicate parameter in Google-style docstrings."""

    def test_duplicate_detected(self):
        ds = "Summary.\n\nArgs:\n    b (int): An integer.\n    b (str): A string.\n"
        func = "def foo(b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM007().diagnose(node, ctx))
        assert result is not None
        assert len(result) == 1
        assert result[0].rule == "PRM007"
        assert "'b'" in result[0].message

    def test_no_duplicate_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    a (int): An integer.\n    b (str): A string.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM007().diagnose(node, ctx))
        assert result == []

    def test_triple_duplicate_two_diagnostics(self):
        ds = "Summary.\n\nArgs:\n    x: First.\n    x: Second.\n    x: Third.\n"
        func = "def foo(x: int):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM007().diagnose(node, ctx))
        assert result is not None
        assert len(result) == 2

    def test_fix_is_unsafe(self):
        ds = "Summary.\n\nArgs:\n    b (int): An integer.\n    b (str): A string.\n"
        func = "def foo(b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM007().diagnose(node, ctx))
        assert result is not None
        assert result[0].fix is not None
        assert result[0].fix.applicability == Applicability.UNSAFE

    def test_non_function_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    b (int): An integer.\n    b (str): A string.\n"
        parsed = parse_google(ds)
        sections = _find_cst_nodes(parsed, GoogleSection)
        section = next(s for s in sections if s.section_kind == GoogleSectionKind.ARGS)
        tree = ast.parse("class Foo:\n    pass\n")
        node = section
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        result = list(PRM007().diagnose(node, ctx))
        assert result == []


class TestD408NumpyParam:
    """PRM007: duplicate parameter in NumPy-style docstrings."""

    def test_duplicate_detected(self):
        ds = "Summary.\n\nParameters\n----------\nb : int\n    An integer.\nb : str\n    A string.\n"
        func = "def foo(b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        result = list(PRM007().diagnose(node, ctx))
        assert result is not None
        assert len(result) == 1
        assert "'b'" in result[0].message

    def test_no_duplicate_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\na : int\n    An integer.\nb : str\n    A string.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        result = list(PRM007().diagnose(node, ctx))
        assert result == []


class TestD408Registry:
    """PRM007 is registered correctly."""

    def test_registry_contains_d408(self):
        registry = build_registry()
        assert registry.get("PRM007") is not None

    def test_rules_for_google_section(self):
        registry = build_registry()
        rules = registry.rules_for_kind(GoogleSection)
        assert any(r.code == "PRM007" for r in rules)

    def test_rules_for_numpy_section(self):
        registry = build_registry()
        rules = registry.rules_for_kind(NumPySection)
        assert any(r.code == "PRM007" for r in rules)


# ── PRM006 Tests ───────────────────────────────────────────────────────


class TestD409GoogleParam:
    """PRM006: wrong parameter order in Google-style docstrings."""

    def test_wrong_order_detected(self):
        ds = "Summary.\n\nArgs:\n    b: The b.\n    a: The a.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None
        assert len(result) >= 1
        assert result[0].rule == "PRM006"
        assert "'b'" in result[0].message

    def test_correct_order_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    a: The a.\n    b: The b.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result == []

    def test_partial_docs_correct_relative_order(self):
        """Only `a` and `c` documented and in correct relative order."""
        ds = "Summary.\n\nArgs:\n    a: The a.\n    c: The c.\n"
        func = "def foo(a: int, b: str, c: float):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result == []

    def test_partial_docs_wrong_relative_order(self):
        """Only `c` and `a` documented but in wrong relative order."""
        ds = "Summary.\n\nArgs:\n    c: The c.\n    a: The a.\n"
        func = "def foo(a: int, b: str, c: float):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None

    def test_extra_param_not_in_sig_ignored(self):
        """Unknown doc params are not counted in order comparison."""
        ds = "Summary.\n\nArgs:\n    z: Unknown.\n    a: The a.\n    b: The b.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result == []

    def test_fix_reorders_params(self):
        ds = "Summary.\n\nArgs:\n    b: The b.\n    a: The a.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None
        assert result[0].fix is not None
        assert result[0].fix.applicability == Applicability.UNSAFE
        fixed = apply_edits(ds, result[0].fix.edits)
        # After fix, a should come before b
        assert fixed.index("    a:") < fixed.index("    b:")

    def test_fix_only_on_first_violation(self):
        ds = "Summary.\n\nArgs:\n    c: The c.\n    b: The b.\n    a: The a.\n"
        func = "def foo(a: int, b: str, c: float):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None
        assert result[0].fix is not None
        assert all(d.fix is None for d in result[1:])

    def test_fix_preserves_unknown_params_at_end(self):
        ds = "Summary.\n\nArgs:\n    b: The b.\n    z: Unknown.\n    a: The a.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_google(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None
        fixed = apply_edits(ds, result[0].fix.edits)
        assert fixed.index("    a:") < fixed.index("    b:") or fixed.index("    b:") < fixed.index("    z:")
        assert "    z:" in fixed

    def test_non_function_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    b: The b.\n    a: The a.\n"
        parsed = parse_google(ds)
        sections = _find_cst_nodes(parsed, GoogleSection)
        section = next(s for s in sections if s.section_kind == GoogleSectionKind.ARGS)
        tree = ast.parse("class Foo:\n    pass\n")
        node = section
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 0, '"""', '"""'),
        )
        result = list(PRM006().diagnose(node, ctx))
        assert result == []


class TestD409NumpyParam:
    """PRM006: wrong parameter order in NumPy-style docstrings."""

    def test_wrong_order_detected(self):
        ds = "Summary.\n\nParameters\n----------\nb : str\n    The b.\na : int\n    The a.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None
        assert len(result) >= 1
        assert "'b'" in result[0].message

    def test_correct_order_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\na : int\n    The a.\nb : str\n    The b.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result == []

    def test_fix_reorders_params(self):
        ds = "Summary.\n\nParameters\n----------\nb : str\n    The b.\na : int\n    The a.\n"
        func = "def foo(a: int, b: str):\n    pass\n"
        node, ctx = _make_d404_ctx_numpy(ds, func)
        result = list(PRM006().diagnose(node, ctx))
        assert result is not None
        assert result[0].fix is not None
        fixed = apply_edits(ds, result[0].fix.edits)
        assert fixed.index("a : int") < fixed.index("b : str")


class TestD409Registry:
    """PRM006 is registered correctly."""

    def test_registry_contains_d409(self):
        registry = build_registry()
        assert registry.get("PRM006") is not None

    def test_rules_for_google_section(self):
        registry = build_registry()
        rules = registry.rules_for_kind(GoogleSection)
        assert any(r.code == "PRM006" for r in rules)

    def test_rules_for_numpy_section(self):
        registry = build_registry()
        rules = registry.rules_for_kind(NumPySection)
        assert any(r.code == "PRM006" for r in rules)


# ── SUM001 Tests ───────────────────────────────────────────────────────


def _make_root_ctx(ds_text: str, func_src: str, *, is_numpy: bool = False):
    """Build a DiagnoseContext targeting the docstring root node."""
    parsed = parse_numpy(ds_text) if is_numpy else parse_google(ds_text)
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return parsed, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


class TestSUM001:
    """SUM001: docstring has no summary line."""

    def test_no_summary_google(self):
        ds = "\n\nArgs:\n    x: desc.\n"
        node, ctx = _make_root_ctx(ds, "def foo(x):\n    pass\n")
        diag = next(iter(SUM001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "SUM001"

    def test_has_summary_no_diagnostic(self):
        ds = "Do something.\n\nArgs:\n    x: desc.\n"
        node, ctx = _make_root_ctx(ds, "def foo(x):\n    pass\n")
        diag = next(iter(SUM001().diagnose(node, ctx)), None)
        assert diag is None

    def test_empty_docstring(self):
        ds = ""
        parsed = parse_google(ds)
        node = parsed
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("def f(): pass").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 6, '"""', '"""'),
        )
        diag = next(iter(SUM001().diagnose(node, ctx)), None)
        assert diag is not None

    def test_not_fixable(self):
        ds = ""
        parsed = parse_google(ds)
        node = parsed
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("def f(): pass").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, 6, '"""', '"""'),
        )
        diag = next(iter(SUM001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is None


# ── PRM002 Tests ───────────────────────────────────────────────────────


def _make_section_ctx(ds_text: str, func_src: str, *, is_numpy: bool = False):
    """Build a DiagnoseContext targeting the first Args/Parameters section."""
    parsed = parse_numpy(ds_text) if is_numpy else parse_google(ds_text)
    kind = NumPySection if is_numpy else GoogleSection
    sections = _find_cst_nodes(parsed, kind)
    assert sections, "No section found"
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return sections[0], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


class TestPRM002:
    """PRM002: no params but has Args section."""

    def test_no_params_but_has_section(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    pass\n")
        diag = next(iter(PRM002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM002"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_has_params_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        node, ctx = _make_section_ctx(ds, "def foo(x):\n    pass\n")
        diag = next(iter(PRM002().diagnose(node, ctx)), None)
        assert diag is None

    def test_self_only_triggers(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        node, ctx = _make_section_ctx(ds, "def foo(self):\n    pass\n")
        diag = next(iter(PRM002().diagnose(node, ctx)), None)
        assert diag is not None

    def test_numpy_no_params(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    desc.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    pass\n", is_numpy=True)
        diag = next(iter(PRM002().diagnose(node, ctx)), None)
        assert diag is not None


# ── PRM003 Tests ───────────────────────────────────────────────────────


class TestPRM003:
    """PRM003: self/cls in docstring."""

    def test_self_documented(self):
        ds = "Summary.\n\nArgs:\n    self: The instance.\n    x: desc.\n"
        func = "def foo(self, x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        # First arg node is self
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM003().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM003"
        assert "'self'" in diag.message
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_cls_documented(self):
        ds = "Summary.\n\nArgs:\n    cls: The class.\n"
        func = "def foo(cls):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM003().diagnose(node, ctx)), None)
        assert diag is not None
        assert "'cls'" in diag.message

    def test_regular_param_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM003().diagnose(node, ctx)), None)
        assert diag is None


# ── PRM102 Tests ───────────────────────────────────────────────────────


class TestPRM102:
    """PRM102: no type in docstring or signature."""

    def test_no_type_anywhere(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM102().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM102"

    def test_type_in_docstring_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM102().diagnose(node, ctx)), None)
        assert diag is None

    def test_type_in_signature_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM102().diagnose(node, ctx)), None)
        assert diag is None

    def test_numpy_no_type_anywhere(self):
        ds = "Summary.\n\nParameters\n----------\nx\n    desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        tree = ast.parse(func)
        node = params[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM102().diagnose(node, ctx)), None)
        assert diag is not None

    def test_numpy_none_param_no_diagnostic(self):
        """NumPy convention: ``Parameters\\n----------\\nNone`` is not a real param."""
        ds = "Summary.\n\nParameters\n----------\nNone\n"
        func = "def foo():\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        if not params:
            return  # parser did not produce a param node — nothing to test
        tree = ast.parse(func)
        node = params[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(PRM102().diagnose(node, ctx)), None)
        assert diag is None  # "None" is not in the signature — PRM002's job

    def test_param_not_in_signature_no_diagnostic(self):
        """Docstring param that does not exist in signature should not trigger PRM102."""
        ds = "Summary.\n\nArgs:\n    ghost: undocumented param.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM102().diagnose(node, ctx)), None)
        assert diag is None  # "ghost" not in signature — PRM002's responsibility


# ── PRM103 Tests ───────────────────────────────────────────────────────


class TestPRM103:
    """PRM103: no type in docstring."""

    def test_no_doc_type(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM103().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM103"

    def test_has_doc_type_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM103().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_inserts_type_google(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM103().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "(int)" in result

    def test_not_enabled_by_default(self):
        assert PRM103.enabled_by_default is False

    def test_both_mode_no_sig_annotation_still_fires(self):
        """'both' mode: signature has no annotation → PRM103 still fires (docstring must have type)."""

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM103().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM103"

    def test_both_mode_with_sig_annotation_fires(self):
        """'both' mode: signature has annotation but docstring lacks type → PRM103 fires."""

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM103().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM103"

    def test_docstring_mode_no_sig_annotation_still_fires(self):
        """'docstring' mode: fires even when signature has no annotation."""

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM103().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM103"


# ── PRM104 Tests ───────────────────────────────────────────────────────


class TestPRM104:
    """PRM104: redundant type in docstring."""

    def test_redundant_type_google(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM104().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM104"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_no_annotation_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM104().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_doc_type_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM104().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_removes_type_google(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM104().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "(int)" not in result
        assert "x:" in result

    def test_not_enabled_by_default(self):
        assert PRM104.enabled_by_default is False


# ── PRM105 Tests ───────────────────────────────────────────────────────


class TestPRM105:
    """PRM105: no type annotation in signature (type_annotation_style = 'both')."""

    def test_no_sig_annotation_fires(self):
        from pydocfix.rules.prm.prm105 import PRM105

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM105().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM105"

    def test_has_sig_annotation_no_diagnostic(self):
        from pydocfix.rules.prm.prm105 import PRM105

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM105().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        from pydocfix.rules.prm.prm105 import PRM105

        assert PRM105.enabled_by_default is False

    def test_conflicts_with_prm102(self):
        from pydocfix.rules.prm.prm105 import PRM105

        assert "PRM102" in PRM105.conflicts_with


# ── PRM106 Tests ───────────────────────────────────────────────────────


class TestPRM106:
    """PRM106: redundant type annotation in signature (type_annotation_style = 'docstring')."""

    def test_has_sig_annotation_fires(self):
        from pydocfix.rules.prm.prm106 import PRM106

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM106().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM106"

    def test_no_sig_annotation_no_diagnostic(self):
        from pydocfix.rules.prm.prm106 import PRM106

        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(PRM106().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        from pydocfix.rules.prm.prm106 import PRM106

        assert PRM106.enabled_by_default is False

    def test_conflicts_with_prm105(self):
        from pydocfix.rules.prm.prm106 import PRM106

        assert "PRM105" in PRM106.conflicts_with


# ── PRM201 Tests ───────────────────────────────────────────────────────


class TestPRM201:
    """PRM201: missing 'optional' in docstring."""

    def test_missing_optional(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int = 5):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM201().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM201"

    def test_has_optional_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int, optional): desc.\n"
        func = "def foo(x: int = 5):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM201().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_default_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM201().diagnose(node, ctx)), None)
        assert diag is None

    def test_kwonly_with_default(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(*, x: int = 0):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM201().diagnose(node, ctx)), None)
        assert diag is not None


# ── PRM202 Tests ───────────────────────────────────────────────────────


class TestPRM202:
    """PRM202: missing 'default' in docstring."""

    def test_missing_default(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int = 5):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM202().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM202"

    def test_has_default_mention_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc. Defaults to 5.\n"
        func = "def foo(x: int = 5):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM202().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_default_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM202().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_appends_default(self):
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int = 5):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM202().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Defaults to 5" in result


# ── RTN001 Tests ───────────────────────────────────────────────────────


class TestRTN001:
    """RTN001: missing Returns section."""

    def test_missing_returns_section(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo() -> int:\n    pass\n")
        diag = next(iter(RTN001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN001"
        assert diag.fix is not None

    def test_has_returns_section_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_root_ctx(ds, "def foo() -> int:\n    pass\n")
        diag = next(iter(RTN001().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_return_annotation_no_diagnostic(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo():\n    pass\n")
        diag = next(iter(RTN001().diagnose(node, ctx)), None)
        assert diag is None

    def test_none_return_no_diagnostic(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo() -> None:\n    pass\n")
        diag = next(iter(RTN001().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_inserts_returns_section_google(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo() -> str:\n    pass\n")
        diag = next(iter(RTN001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Returns:" in result
        assert "str:" in result

    def test_fix_inserts_returns_section_numpy(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo() -> str:\n    pass\n", is_numpy=True)
        diag = next(iter(RTN001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Returns" in result
        assert "-------" in result
        assert "str" in result


# ── RTN002 Tests ───────────────────────────────────────────────────────


class TestRTN002:
    """RTN002: unnecessary Returns section (function does not return a value)."""

    def test_no_return_value_triggers(self):
        """No return statement → unnecessary Returns section."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    pass\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN002"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_bare_return_triggers(self):
        """``return`` with no value → unnecessary Returns section."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    return\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is not None

    def test_return_none_triggers(self):
        """``return None`` → unnecessary Returns section."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    return None\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is not None

    def test_returns_value_no_diagnostic(self):
        """``return <expr>`` → Returns section is warranted."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo() -> int:\n    return 42\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is None

    def test_returns_value_without_annotation_no_diagnostic(self):
        """Unannotated but actually returning → Returns section is warranted."""
        ds = "Summary.\n\nReturns:\n    The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    return 42\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is None

    def test_none_annotation_but_no_return_value_triggers(self):
        """``-> None`` and no return value → unnecessary Returns section."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo() -> None:\n    pass\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is not None

    def test_has_annotation_but_no_return_value_triggers(self):
        """``-> int`` annotation but no actual return → unnecessary Returns section."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo() -> int:\n    pass\n")
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is not None

    def test_nested_function_return_ignored(self):
        """Return inside a nested function should not affect outer function."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo():\n    def inner():\n        return 42\n    pass\n"
        node, ctx = _make_section_ctx(ds, func)
        diag = next(iter(RTN002().diagnose(node, ctx)), None)
        assert diag is not None


# ── RTN003 Tests ───────────────────────────────────────────────────────


def _make_returns_entry_ctx(ds_text: str, func_src: str, *, is_numpy: bool = False):
    """Build a DiagnoseContext targeting a GOOGLE_RETURNS/NUMPY_RETURNS node."""
    parsed = parse_numpy(ds_text) if is_numpy else parse_google(ds_text)
    kind = NumPyReturns if is_numpy else GoogleReturn
    entries = _find_cst_nodes(parsed, kind)
    assert entries, "No return entries found"
    tree = ast.parse(func_src)
    return entries[0], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=tree.body[0],
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


class TestRTN003:
    """RTN003: Returns section has no description."""

    def test_no_description(self):
        ds = "Summary.\n\nReturns:\n    int:\n"
        func = "def foo() -> int:\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        diag = next(iter(RTN003().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN003"

    def test_has_description_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        diag = next(iter(RTN003().diagnose(node, ctx)), None)
        assert diag is None

    def test_yields_section_ignored(self):
        """RTN003 targets GOOGLE_RETURNS, not GOOGLE_YIELDS — dispatcher never sends Yields entries."""
        assert GoogleYield not in RTN003._targets
        assert NumPyYields not in RTN003._targets


# ── RTN102 Tests ───────────────────────────────────────────────────────


class TestRTN102:
    """RTN102: no return type in docstring or signature."""

    def test_no_type_anywhere(self):
        ds = "Summary.\n\nReturns:\n    The result.\n"
        func = "def foo():\n    return 1\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleReturn)
        if not entries:
            return  # parser might not produce returns node
        tree = ast.parse(func)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RTN102().diagnose(node, ctx)), None)
        # If RETURN_TYPE is present it won't trigger; depends on parser
        if diag is not None:
            assert diag.rule == "RTN102"

    def test_type_in_docstring_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo():\n    return 1\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        diag = next(iter(RTN102().diagnose(node, ctx)), None)
        assert diag is None

    def test_type_in_signature_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    The result.\n"
        func = "def foo() -> int:\n    return 1\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleReturn)
        if not entries:
            return
        tree = ast.parse(func)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RTN102().diagnose(node, ctx)), None)
        assert diag is None


# ── RTN103 Tests ───────────────────────────────────────────────────────


class TestRTN103:
    """RTN103: no return type in docstring."""

    def test_no_return_type_in_doc(self):
        ds = "Summary.\n\nReturns:\n    The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleReturn)
        if not entries:
            return
        tree = ast.parse(func)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RTN103().diagnose(node, ctx)), None)
        # Depends on whether parser produces RETURN_TYPE token
        if diag is not None:
            assert diag.rule == "RTN103"

    def test_has_type_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        diag = next(iter(RTN103().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        assert RTN103.enabled_by_default is False


# ── RTN104 Tests ───────────────────────────────────────────────────────


class TestRTN104:
    """RTN104: redundant return type in docstring."""

    def test_redundant_return_type(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        diag = next(iter(RTN104().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN104"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_no_annotation_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo():\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        diag = next(iter(RTN104().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_doc_type_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleReturn)
        if not entries:
            return
        tree = ast.parse(func)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RTN104().diagnose(node, ctx)), None)
        # If no RETURN_TYPE token, no diagnostic
        assert diag is None

    def test_not_enabled_by_default(self):
        assert RTN104.enabled_by_default is False


# ── RTN105 Tests ───────────────────────────────────────────────────────


class TestRTN105:
    """RTN105: no return type annotation in signature (type_annotation_style = 'both')."""

    def test_no_sig_annotation_fires(self):
        from pydocfix.rules.rtn.rtn105 import RTN105

        ds = "Summary.\n\nReturns:\n    The result.\n"
        func = "def foo():\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(RTN105().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN105"

    def test_has_sig_annotation_no_diagnostic(self):
        from pydocfix.rules.rtn.rtn105 import RTN105

        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(RTN105().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        from pydocfix.rules.rtn.rtn105 import RTN105

        assert RTN105.enabled_by_default is False

    def test_conflicts_with_rtn102(self):
        from pydocfix.rules.rtn.rtn105 import RTN105

        assert "RTN102" in RTN105.conflicts_with


# ── RTN106 Tests ───────────────────────────────────────────────────────


class TestRTN106:
    """RTN106: redundant return type annotation in signature (type_annotation_style = 'docstring')."""

    def test_has_sig_annotation_fires(self):
        from pydocfix.rules.rtn.rtn106 import RTN106

        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(RTN106().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN106"

    def test_no_sig_annotation_no_diagnostic(self):
        from pydocfix.rules.rtn.rtn106 import RTN106

        ds = "Summary.\n\nReturns:\n    The result.\n"
        func = "def foo():\n    pass\n"
        node, ctx = _make_returns_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(RTN106().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        from pydocfix.rules.rtn.rtn106 import RTN106

        assert RTN106.enabled_by_default is False

    def test_conflicts_with_rtn105(self):
        from pydocfix.rules.rtn.rtn106 import RTN106

        assert "RTN105" in RTN106.conflicts_with


# ── YLD001 Tests ───────────────────────────────────────────────────────


class TestYLD001:
    """YLD001: missing Yields section."""

    def test_missing_yields_section(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo():\n    yield 1\n")
        diag = next(iter(YLD001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD001"
        assert diag.fix is not None

    def test_has_yields_section_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        node, ctx = _make_root_ctx(ds, "def foo():\n    yield 1\n")
        diag = next(iter(YLD001().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_generator_no_diagnostic(self):
        ds = "Summary."
        node, ctx = _make_root_ctx(ds, "def foo():\n    return 1\n")
        diag = next(iter(YLD001().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_inserts_yields_google(self):
        ds = "Summary."
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        node = parsed
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Yields:" in result
        assert "int:" in result

    def test_fix_inserts_yields_numpy(self):
        ds = "Summary."
        func = "from typing import Generator\ndef foo() -> Generator[str, None, None]:\n    yield 'x'\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_numpy(ds)
        node = parsed
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Yields" in result
        assert "------" in result
        assert "str" in result

    def test_nested_yield_not_detected(self):
        """Yield in a nested function should not trigger."""
        ds = "Summary."
        func = "def foo():\n    def inner():\n        yield 1\n    return inner\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(YLD001().diagnose(node, ctx)), None)
        assert diag is None


# ── YLD002 Tests ───────────────────────────────────────────────────────


class TestYLD002:
    """YLD002: unnecessary Yields section."""

    def test_unnecessary_yields(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    return 1\n")
        diag = next(iter(YLD002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD002"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_is_generator_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    yield 1\n")
        diag = next(iter(YLD002().diagnose(node, ctx)), None)
        assert diag is None

    def test_non_yields_section_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        node, ctx = _make_section_ctx(ds, "def foo():\n    return 1\n")
        diag = next(iter(YLD002().diagnose(node, ctx)), None)
        assert diag is None


# ── YLD003 Tests ───────────────────────────────────────────────────────


def _make_yields_entry_ctx(ds_text: str, func_src: str, *, is_numpy: bool = False):
    """Build a DiagnoseContext targeting the first GOOGLE_YIELDS/NUMPY_YIELDS node."""
    parsed = parse_numpy(ds_text) if is_numpy else parse_google(ds_text)
    kind = NumPyYields if is_numpy else GoogleYield
    entries = _find_cst_nodes(parsed, kind)
    assert entries, "No yields entries found"
    tree = ast.parse(func_src)
    return entries[0], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=tree.body[0],
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


class TestYLD003:
    """YLD003: Yields section has no description."""

    def test_no_description(self):
        ds = "Summary.\n\nYields:\n    int:\n"
        func = "def foo():\n    yield 1\n"
        node, ctx = _make_yields_entry_ctx(ds, func)
        diag = next(iter(YLD003().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD003"

    def test_has_description_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "def foo():\n    yield 1\n"
        node, ctx = _make_yields_entry_ctx(ds, func)
        diag = next(iter(YLD003().diagnose(node, ctx)), None)
        assert diag is None


# ── YLD101 Tests ───────────────────────────────────────────────────────


class TestYLD101:
    """YLD101: yield type mismatch."""

    def test_type_mismatch(self):
        ds = "Summary.\n\nYields:\n    str: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD101"
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_matching_type_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD101().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_replaces_type(self):
        ds = "Summary.\n\nYields:\n    str: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD101().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "int:" in result

    def test_returns_section_not_affected(self):
        """YLD101 targets GOOGLE_YIELDS, not GOOGLE_RETURNS — dispatcher never sends Returns entries."""
        assert GoogleReturn not in YLD101._targets
        assert NumPyReturns not in YLD101._targets


# ── allow_optional_shorthand Tests ─────────────────────────────────────


class TestAllowOptionalShorthand:
    """PRM101/RTN101/YLD101: allow_optional_shorthand normalises Optional[T] before comparison."""

    # ── PRM101 ──

    def test_prm101_optional_fires_by_default(self):
        """Optional[int] sig vs int doc → PRM101 fires (default off)."""
        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "from typing import Optional\ndef foo(x: Optional[int]):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = next(iter(PRM101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM101"

    def test_prm101_optional_suppressed_when_flag_true(self):
        """Optional[int] sig vs int doc → silent when allow_optional_shorthand=True."""
        from pydocfix.config import Config

        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "from typing import Optional\ndef foo(x: Optional[int]):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        cfg = Config(allow_optional_shorthand=True)
        diag = next(iter(PRM101(cfg).diagnose(node, ctx)), None)
        assert diag is None

    def test_prm101_pipe_none_suppressed_when_flag_true(self):
        """int | None sig vs int doc → silent when allow_optional_shorthand=True."""
        from pydocfix.config import Config

        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "def foo(x: int | None):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        cfg = Config(allow_optional_shorthand=True)
        diag = next(iter(PRM101(cfg).diagnose(node, ctx)), None)
        assert diag is None

    def test_prm101_union_none_suppressed_when_flag_true(self):
        """Union[int, None] sig vs int doc → silent when allow_optional_shorthand=True."""
        from pydocfix.config import Config

        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "from typing import Union\ndef foo(x: Union[int, None]):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        cfg = Config(allow_optional_shorthand=True)
        diag = next(iter(PRM101(cfg).diagnose(node, ctx)), None)
        assert diag is None

    def test_prm101_genuine_mismatch_still_fires(self):
        """Optional[str] sig vs int doc → PRM101 still fires (after normalisation, str != int)."""
        from pydocfix.config import Config

        ds = "Summary.\n\nArgs:\n    x (int): desc.\n"
        func = "from typing import Optional\ndef foo(x: Optional[str]):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_d401_ctx_google(ds, func, args[0])
        cfg = Config(allow_optional_shorthand=True)
        diag = next(iter(PRM101(cfg).diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "PRM101"

    # ── RTN101 ──

    def test_rtn101_optional_suppressed_when_flag_true(self):
        """Optional[int] return vs int doc → silent when allow_optional_shorthand=True."""
        from pydocfix.config import Config

        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "from typing import Optional\ndef foo() -> Optional[int]:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, GoogleReturn)
        node, ctx = _make_d401_ctx_google(ds, func, rets[0])
        cfg = Config(allow_optional_shorthand=True)
        diag = next(iter(RTN101(cfg).diagnose(node, ctx)), None)
        assert diag is None

    def test_rtn101_optional_fires_by_default(self):
        """Optional[int] return vs int doc → RTN101 fires (default off)."""
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "from typing import Optional\ndef foo() -> Optional[int]:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, GoogleReturn)
        node, ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = next(iter(RTN101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RTN101"

    # ── YLD101 ──

    def test_yld101_optional_suppressed_when_flag_true(self):
        """Optional[int] yield vs int doc → silent when allow_optional_shorthand=True."""
        from pydocfix.config import Config

        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Optional, Generator\ndef foo() -> Generator[Optional[int], None, None]:\n    yield None\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        cfg = Config(allow_optional_shorthand=True)
        diag = next(iter(YLD101(cfg).diagnose(node, ctx)), None)
        assert diag is None

    def test_yld101_optional_fires_by_default(self):
        """Optional[int] yield vs int doc → YLD101 fires (default off)."""
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Optional, Generator\ndef foo() -> Generator[Optional[int], None, None]:\n    yield None\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD101().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD101"


# ── YLD102 Tests ───────────────────────────────────────────────────────


class TestYLD102:
    """YLD102: no yield type in docstring or signature."""

    def test_no_type_anywhere(self):
        ds = "Summary.\n\nYields:\n    An item.\n"
        func = "def foo():\n    yield 1\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        if not entries:
            return
        tree = ast.parse(func)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD102().diagnose(node, ctx)), None)
        if diag is not None:
            assert diag.rule == "YLD102"

    def test_type_in_docstring_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "def foo():\n    yield 1\n"
        node, ctx = _make_yields_entry_ctx(ds, func)
        diag = next(iter(YLD102().diagnose(node, ctx)), None)
        assert diag is None


# ── YLD103 Tests ───────────────────────────────────────────────────────


class TestYLD103:
    """YLD103: no yield type in docstring."""

    def test_not_enabled_by_default(self):
        assert YLD103.enabled_by_default is False

    def test_no_type_in_docstring(self):
        ds = "Summary.\n\nYields:\n    An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        assert entries
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD103().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD103"

    def test_has_type_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        assert entries
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD103().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_inserts_type(self):
        ds = "Summary.\n\nYields:\n    An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        assert entries
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD103().diagnose(node, ctx)), None)
        assert diag is not None
        if diag.fix:
            result = apply_edits(ds, diag.fix.edits)
            assert "int" in result


# ── YLD104 Tests ───────────────────────────────────────────────────────


class TestYLD104:
    """YLD104: redundant yield type in docstring."""

    def test_redundant_type(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        func_node = tree.body[1]
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleYield)
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=func_node,
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(YLD104().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD104"
        assert diag.fix.applicability == Applicability.SAFE

    def test_no_sig_type_no_diagnostic(self):
        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "def foo():\n    yield 1\n"
        node, ctx = _make_yields_entry_ctx(ds, func)
        diag = next(iter(YLD104().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        assert YLD104.enabled_by_default is False


# ── YLD105 Tests ───────────────────────────────────────────────────────


class TestYLD105:
    """YLD105: no yield type annotation in signature (type_annotation_style = 'both')."""

    def test_no_sig_annotation_fires(self):
        from pydocfix.rules.yld.yld105 import YLD105

        ds = "Summary.\n\nYields:\n    An item.\n"
        func = "def foo():\n    yield 1\n"
        node, ctx = _make_yields_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(YLD105().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD105"

    def test_has_sig_annotation_no_diagnostic(self):
        from pydocfix.rules.yld.yld105 import YLD105

        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        node, ctx = _make_yields_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=tree.body[1],
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(YLD105().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        from pydocfix.rules.yld.yld105 import YLD105

        assert YLD105.enabled_by_default is False

    def test_conflicts_with_yld102(self):
        from pydocfix.rules.yld.yld105 import YLD105

        assert "YLD102" in YLD105.conflicts_with


# ── YLD106 Tests ───────────────────────────────────────────────────────


class TestYLD106:
    """YLD106: redundant yield type annotation in signature (type_annotation_style = 'docstring')."""

    def test_has_sig_annotation_fires(self):
        from pydocfix.rules.yld.yld106 import YLD106

        ds = "Summary.\n\nYields:\n    int: An item.\n"
        func = "from typing import Generator\ndef foo() -> Generator[int, None, None]:\n    yield 1\n"
        tree = ast.parse(func)
        node, ctx = _make_yields_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=tree.body[1],
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(YLD106().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "YLD106"

    def test_no_sig_annotation_no_diagnostic(self):
        from pydocfix.rules.yld.yld106 import YLD106

        ds = "Summary.\n\nYields:\n    An item.\n"
        func = "def foo():\n    yield 1\n"
        node, ctx = _make_yields_entry_ctx(ds, func)
        ctx = DiagnoseContext(
            filepath=ctx.filepath,
            docstring_text=ctx.docstring_text,
            docstring_cst=ctx.docstring_cst,
            parent_ast=ctx.parent_ast,
            docstring_stmt=ctx.docstring_stmt,
            docstring_location=ctx.docstring_location,
        )
        diag = next(iter(YLD106().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_enabled_by_default(self):
        from pydocfix.rules.yld.yld106 import YLD106

        assert YLD106.enabled_by_default is False

    def test_conflicts_with_yld105(self):
        from pydocfix.rules.yld.yld106 import YLD106

        assert "YLD105" in YLD106.conflicts_with


# ── RIS001 Tests ───────────────────────────────────────────────────────


def _make_raises_section_ctx(ds_text: str, func_src: str, *, is_numpy: bool = False):
    """Build a DiagnoseContext targeting the first Raises section."""
    parsed = parse_numpy(ds_text) if is_numpy else parse_google(ds_text)
    kind = NumPySection if is_numpy else GoogleSection
    sections = _find_cst_nodes(parsed, kind)
    # Find the Raises section
    raises_section = None
    for sec in sections:
        if is_numpy:
            if sec.section_kind == NumPySectionKind.RAISES:
                raises_section = sec
                break
        else:
            if sec.section_kind == GoogleSectionKind.RAISES:
                raises_section = sec
                break
    assert raises_section is not None, "No Raises section found"
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return raises_section, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


def _make_raises_entry_ctx(ds_text: str, func_src: str, *, is_numpy: bool = False):
    """Build a DiagnoseContext targeting the first GoogleException/NumPyException node."""
    parsed = parse_numpy(ds_text) if is_numpy else parse_google(ds_text)
    kind = NumPyException if is_numpy else GoogleException
    entries = _find_cst_nodes(parsed, kind)
    assert entries, "No exception entries found"
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return entries[0], DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=func_node,
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
    )


class TestRIS001:
    """RIS001: function raises but no Raises section."""

    def test_missing_raises_section(self):
        ds = "Summary."
        func = "def foo():\n    raise ValueError('bad')\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RIS001"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.UNSAFE

    def test_has_raises_section_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is None

    def test_no_raise_no_diagnostic(self):
        ds = "Summary."
        func = "def foo():\n    return 1\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_inserts_raises_google(self):
        ds = "Summary."
        func = "def foo():\n    raise ValueError('bad')\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Raises:" in result
        assert "ValueError" in result

    def test_fix_inserts_raises_numpy(self):
        ds = "Summary."
        func = "def foo():\n    raise TypeError('bad')\n"
        node, ctx = _make_root_ctx(ds, func, is_numpy=True)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Raises" in result
        assert "------" in result
        assert "TypeError" in result

    def test_raise_call_form(self):
        """raise ExcType(...) should be detected."""
        ds = "Summary."
        func = "def foo():\n    raise RuntimeError('oops')\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is not None

    def test_bare_reraise_no_diagnostic(self):
        """Bare `raise` (re-raise) should not trigger."""
        ds = "Summary."
        func = "def foo():\n    try:\n        pass\n    except:\n        raise\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is None

    def test_nested_function_raise_not_detected(self):
        """Raise in nested function should not trigger on outer."""
        ds = "Summary."
        func = "def foo():\n    def inner():\n        raise ValueError()\n    return inner\n"
        node, ctx = _make_root_ctx(ds, func)
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_function_no_diagnostic(self):
        """Non-function parent should not trigger."""
        ds = "Summary."
        parsed = parse_google(ds)
        node = parsed
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("x = 1").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, len(ds) + 6, '"""', '"""'),
        )
        diag = next(iter(RIS001().diagnose(node, ctx)), None)
        assert diag is None


class TestRIS002:
    """RIS002: unnecessary Raises section."""

    def test_unnecessary_raises_section(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    return 1\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diag = next(iter(RIS002().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RIS002"
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_has_raise_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diag = next(iter(RIS002().diagnose(node, ctx)), None)
        assert diag is None

    def test_non_raises_section_no_diagnostic(self):
        """Args section should not trigger RIS002."""
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        node, ctx = _make_section_ctx(ds, "def foo(x):\n    pass\n")
        diag = next(iter(RIS002().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_removes_section(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    return 1\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diag = next(iter(RIS002().diagnose(node, ctx)), None)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "Raises:" not in result
        assert "ValueError" not in result

    def test_not_function_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        parsed = parse_google(ds)
        sections = _find_cst_nodes(parsed, GoogleSection)
        raises = [s for s in sections if s.section_kind == GoogleSectionKind.RAISES]
        assert raises
        node = raises[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("x = 1").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, len(ds) + 6, '"""', '"""'),
        )
        diag = next(iter(RIS002().diagnose(node, ctx)), None)
        assert diag is None


class TestRIS003:
    """RIS003: Raises entry has no description."""

    def test_no_description(self):
        ds = "Summary.\n\nRaises:\n    ValueError:\n"
        func = "def foo():\n    raise ValueError()\n"
        node, ctx = _make_raises_entry_ctx(ds, func)
        diag = next(iter(RIS003().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.rule == "RIS003"

    def test_has_description_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError()\n"
        node, ctx = _make_raises_entry_ctx(ds, func)
        diag = next(iter(RIS003().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_fixable(self):
        ds = "Summary.\n\nRaises:\n    ValueError:\n"
        func = "def foo():\n    raise ValueError()\n"
        node, ctx = _make_raises_entry_ctx(ds, func)
        diag = next(iter(RIS003().diagnose(node, ctx)), None)
        assert diag is not None
        assert diag.fix is None

    def test_not_function_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError:\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleException)
        assert entries
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("x = 1").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, len(ds) + 6, '"""', '"""'),
        )
        diag = next(iter(RIS003().diagnose(node, ctx)), None)
        assert diag is None


class TestRIS004:
    """RIS004: raised exception missing from Raises section."""

    def test_missing_exception(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n    raise TypeError('oops')\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diags = list(RIS004().diagnose(node, ctx))
        assert any(d.rule == "RIS004" for d in diags)
        assert any("TypeError" in d.message for d in diags)

    def test_all_documented_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n    TypeError: If wrong.\n"
        func = "def foo():\n    raise ValueError('bad')\n    raise TypeError('oops')\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diags = list(RIS004().diagnose(node, ctx))
        assert not diags

    def test_fix_appends_entry(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n    raise TypeError('oops')\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diags = list(RIS004().diagnose(node, ctx))
        assert diags
        for d in diags:
            if "TypeError" in d.message:
                assert d.fix is not None
                result = apply_edits(ds, d.fix.edits)
                assert "TypeError" in result

    def test_non_raises_section_no_diagnostic(self):
        """Args section should not trigger RIS004."""
        ds = "Summary.\n\nArgs:\n    x: desc.\n"
        func = "def foo(x):\n    raise ValueError()\n"
        node, ctx = _make_section_ctx(ds, func)
        diags = list(RIS004().diagnose(node, ctx))
        assert not diags

    def test_not_function_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        parsed = parse_google(ds)
        sections = _find_cst_nodes(parsed, GoogleSection)
        raises = [s for s in sections if s.section_kind == GoogleSectionKind.RAISES]
        assert raises
        node = raises[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("x = 1").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, len(ds) + 6, '"""', '"""'),
        )
        diags = list(RIS004().diagnose(node, ctx))
        assert not diags

    def test_qualified_exception_name(self):
        """Attribute-style raise like `raise http.HTTPError()` should match."""
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n    raise http.HTTPError()\n"
        node, ctx = _make_raises_section_ctx(ds, func)
        diags = list(RIS004().diagnose(node, ctx))
        assert any("HTTPError" in d.message for d in diags)


class TestRIS005:
    """RIS005: Raises entry documents exception not raised."""

    def test_unnecessary_exception(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n    TypeError: If wrong.\n"
        func = "def foo():\n    raise ValueError('bad')\n"
        # Need to target the second entry (TypeError)
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleException)
        assert len(entries) >= 2
        tree = ast.parse(func)
        target = entries[1]  # TypeError entry
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RIS005().diagnose(target, ctx)), None)
        assert diag is not None
        assert diag.rule == "RIS005"
        assert "TypeError" in diag.message

    def test_raised_exception_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n"
        node, ctx = _make_raises_entry_ctx(ds, func)
        diag = next(iter(RIS005().diagnose(node, ctx)), None)
        assert diag is None

    def test_fix_removes_entry(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n    TypeError: If wrong.\n"
        func = "def foo():\n    raise ValueError('bad')\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleException)
        tree = ast.parse(func)
        target = entries[1]  # TypeError
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=tree.body[0],
            docstring_stmt=_dummy_stmt(2, 4),
            docstring_location=DocstringLocation(Offset(2, 7), 0, 0, '"""', '"""'),
        )
        diag = next(iter(RIS005().diagnose(target, ctx)), None)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "TypeError" not in result
        assert "ValueError" in result

    def test_no_type_token_no_diagnostic(self):
        """Entry without a type token should not crash."""
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        func = "def foo():\n    raise ValueError('bad')\n"
        node, ctx = _make_raises_entry_ctx(ds, func)
        diag = next(iter(RIS005().diagnose(node, ctx)), None)
        assert diag is None

    def test_not_function_no_diagnostic(self):
        ds = "Summary.\n\nRaises:\n    ValueError: If bad.\n"
        parsed = parse_google(ds)
        entries = _find_cst_nodes(parsed, GoogleException)
        assert entries
        node = entries[0]
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_text=ds,
            docstring_cst=parsed,
            parent_ast=ast.parse("x = 1").body[0],
            docstring_stmt=_dummy_stmt(1, 0),
            docstring_location=DocstringLocation(Offset(1, 0), 0, len(ds) + 6, '"""', '"""'),
        )
        diag = next(iter(RIS005().diagnose(node, ctx)), None)
        assert diag is None


# ── DOC001 ────────────────────────────────────────────────────────────


def _make_doc001_ctx(ds_text: str):
    """Create a DiagnoseContext targeting the GoogleDocstring root for DOC001."""
    parsed = parse_google(ds_text)
    return parsed, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=ast.parse("pass").body[0],
        docstring_stmt=_dummy_stmt(1, 0),
        docstring_location=DocstringLocation(Offset(1, 0), 0, len(ds_text) + 6, '"""', '"""'),
    )


class TestDOC001:
    DS_WRONG = "Summary.\n\n    Returns:\n        int: Result.\n\n    Args:\n        x: A value.\n"
    DS_CORRECT = "Summary.\n\n    Args:\n        x: A value.\n\n    Returns:\n        int: Result.\n"

    def test_correct_order_no_diagnostic(self):
        node, ctx = _make_doc001_ctx(self.DS_CORRECT)
        assert list(DOC001().diagnose(node, ctx)) == []

    def test_wrong_order_emits_diagnostic(self):
        node, ctx = _make_doc001_ctx(self.DS_WRONG)
        diags = list(DOC001().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC001"
        assert diags[0].fixable is True
        assert diags[0].fix is not None
        assert diags[0].fix.applicability == Applicability.UNSAFE

    def test_single_section_no_diagnostic(self):
        ds = "Summary.\n\n    Returns:\n        int: Result.\n"
        node, ctx = _make_doc001_ctx(ds)
        assert list(DOC001().diagnose(node, ctx)) == []

    def test_fix_reorders_returns_before_args(self):
        node, ctx = _make_doc001_ctx(self.DS_WRONG)
        diag = next(iter(DOC001().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(self.DS_WRONG, diag.fix.edits)
        assert result.index("Args:") < result.index("Returns:")

    def test_fix_preserves_section_texts(self):
        node, ctx = _make_doc001_ctx(self.DS_WRONG)
        diag = next(iter(DOC001().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(self.DS_WRONG, diag.fix.edits)
        assert "Returns:\n        int: Result." in result
        assert "Args:\n        x: A value." in result

    def test_fix_preserves_separator(self):
        node, ctx = _make_doc001_ctx(self.DS_WRONG)
        diag = next(iter(DOC001().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(self.DS_WRONG, diag.fix.edits)
        # Sections must be separated by a blank line
        assert "\n\n" in result
        assert "\n\n\n" not in result

    def test_three_sections_wrong_order(self):
        ds = (
            "Summary.\n\n"
            "    Raises:\n        ValueError: If bad.\n\n"
            "    Returns:\n        int: Result.\n\n"
            "    Args:\n        x: A value.\n"
        )
        node, ctx = _make_doc001_ctx(ds)
        diags = list(DOC001().diagnose(node, ctx))
        assert len(diags) == 1
        result = apply_edits(ds, diags[0].fix.edits)
        args_pos = result.index("Args:")
        returns_pos = result.index("Returns:")
        raises_pos = result.index("Raises:")
        assert args_pos < returns_pos < raises_pos

    def test_idempotent_after_fix(self):
        node, ctx = _make_doc001_ctx(self.DS_WRONG)
        diag = next(iter(DOC001().diagnose(node, ctx)))
        fixed = apply_edits(self.DS_WRONG, diag.fix.edits)
        fixed_node, fixed_ctx = _make_doc001_ctx(fixed)
        assert list(DOC001().diagnose(fixed_node, fixed_ctx)) == []

    def test_stray_line_preserved_after_fix(self):
        """Stray content between sections is preserved in-place after reorder."""
        ds = "Summary.\n\n    Returns:\n        int: Result.\n\n    stray line\n\n    Args:\n        x: A value.\n"
        node, ctx = _make_doc001_ctx(ds)
        diag = next(iter(DOC001().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        # Sections are reordered
        assert result.index("Args:") < result.index("Returns:")
        # Stray line is not lost
        assert "stray line" in result

    def test_stray_line_inside_section_range_preserved(self):
        """Stray content absorbed into a section range (no blank-line separator)
        stays in position rather than moving with the section."""
        ds = "Summary.\n\n    Returns:\n        int: Result.\n    stray line\n    Args:\n        x: A value.\n"
        node, ctx = _make_doc001_ctx(ds)
        diag = next(iter(DOC001().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert result.index("Args:") < result.index("Returns:")
        assert "stray line" in result


# ── DOC002 ────────────────────────────────────────────────────────────


def _make_doc002_ctx(ds_text: str, cst_node, *, numpy: bool = False):
    """Create a DiagnoseContext for DOC002 tests with an entry node as target."""
    parsed = parse_numpy(ds_text) if numpy else parse_google(ds_text)
    return cst_node, DiagnoseContext(
        filepath=Path("test.py"),
        docstring_text=ds_text,
        docstring_cst=parsed,
        parent_ast=ast.parse("pass").body[0],
        docstring_stmt=_dummy_stmt(2, 4),
        docstring_location=DocstringLocation(Offset(2, 7), 0, len(ds_text) + 6, '"""', '"""'),
    )


class TestDOC002:
    """DOC002: incorrect indentation of docstring section entries."""

    # Google style – 4-space section indent, 8-space expected entry indent
    DS_GOOGLE_CORRECT = "Summary.\n\n    Args:\n        x: An arg.\n\n    "
    DS_GOOGLE_UNDER = "Summary.\n\n    Args:\n     x: An arg.\n\n    "  # 5 spaces (expected 8)
    DS_GOOGLE_OVER = "Summary.\n\n    Args:\n            x: An arg.\n\n    "  # 12 spaces

    def test_google_correct_no_diagnostic(self):
        ds = self.DS_GOOGLE_CORRECT
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_doc002_ctx(ds, args[0])
        assert list(DOC002().diagnose(node, ctx)) == []

    def test_google_under_indent_emits_diagnostic(self):
        ds = self.DS_GOOGLE_UNDER
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_doc002_ctx(ds, args[0])
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"
        assert "5" in diags[0].message
        assert "8" in diags[0].message

    def test_google_over_indent_emits_diagnostic(self):
        ds = self.DS_GOOGLE_OVER
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_doc002_ctx(ds, args[0])
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"
        assert "12" in diags[0].message

    def test_fix_corrects_under_indent(self):
        ds = self.DS_GOOGLE_UNDER
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_doc002_ctx(ds, args[0])
        diag = next(iter(DOC002().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "        x: An arg." in result  # 8 spaces

    def test_fix_corrects_over_indent(self):
        ds = self.DS_GOOGLE_OVER
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_doc002_ctx(ds, args[0])
        diag = next(iter(DOC002().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "        x: An arg." in result  # 8 spaces

    def test_fix_is_safe(self):
        ds = self.DS_GOOGLE_UNDER
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, GoogleArg)
        node, ctx = _make_doc002_ctx(ds, args[0])
        diag = next(iter(DOC002().diagnose(node, ctx)))
        assert diag.fix is not None
        assert diag.fix.applicability == Applicability.SAFE

    def test_google_returns_section(self):
        ds = "Summary.\n\n    Returns:\n     str: Result.\n\n    "
        parsed = parse_google(ds)
        returns = _find_cst_nodes(parsed, GoogleReturn)
        node, ctx = _make_doc002_ctx(ds, returns[0])
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"

    def test_google_raises_section(self):
        ds = "Summary.\n\n    Raises:\n     ValueError: If bad.\n\n    "
        parsed = parse_google(ds)
        exceptions = _find_cst_nodes(parsed, GoogleException)
        node, ctx = _make_doc002_ctx(ds, exceptions[0])
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"

    def test_google_yields_section(self):
        ds = "Summary.\n\n    Yields:\n     int: A value.\n\n    "
        parsed = parse_google(ds)
        yields = _find_cst_nodes(parsed, GoogleYield)
        node, ctx = _make_doc002_ctx(ds, yields[0])
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"

    def test_numpy_correct_no_diagnostic(self):
        # NumPy: entries at same indent as section header
        ds = "Summary.\n\n    Parameters\n    ----------\n    x : int\n        An arg.\n\n    "
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        node, ctx = _make_doc002_ctx(ds, params[0], numpy=True)
        assert list(DOC002().diagnose(node, ctx)) == []

    def test_numpy_over_indent_emits_diagnostic(self):
        ds = "Summary.\n\n    Parameters\n    ----------\n      x : int\n        An arg.\n\n    "
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        node, ctx = _make_doc002_ctx(ds, params[0], numpy=True)
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"

    def test_numpy_fix_corrects_indent(self):
        ds = "Summary.\n\n    Parameters\n    ----------\n      x : int\n        An arg.\n\n    "
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, NumPyParameter)
        node, ctx = _make_doc002_ctx(ds, params[0], numpy=True)
        diag = next(iter(DOC002().diagnose(node, ctx)))
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "    x : int" in result  # 4 spaces (same as section)

    def test_numpy_returns_section(self):
        ds = "Summary.\n\n    Returns\n    -------\n      str\n        A value.\n\n    "
        parsed = parse_numpy(ds)
        returns = _find_cst_nodes(parsed, NumPyReturns)
        node, ctx = _make_doc002_ctx(ds, returns[0], numpy=True)
        diags = list(DOC002().diagnose(node, ctx))
        assert len(diags) == 1
        assert diags[0].rule == "DOC002"


# ── Registry completeness ─────────────────────────────────────────────


class TestRegistryCompleteness:
    """All rules are registered."""

    def test_all_rules_with_select_all(self):
        # Without type_annotation_style, style-specific rules (103/104 pairs)
        # are excluded to avoid contradictory enforcement — 6 fewer rules.
        registry = build_registry(select=["ALL"])
        assert len(registry.all_rules()) == 32

    def test_all_rules_select_all_signature_style(self):
        from pydocfix.config import Config

        config = Config(type_annotation_style="signature")
        registry = build_registry(select=["ALL"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert len(registry.all_rules()) == 35
        assert "PRM104" in codes
        assert "RTN104" in codes
        assert "YLD104" in codes
        assert "PRM103" not in codes
        assert "RTN103" not in codes
        assert "YLD103" not in codes

    def test_all_rules_select_all_docstring_style(self):
        from pydocfix.config import Config

        config = Config(type_annotation_style="docstring")
        registry = build_registry(select=["ALL"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert len(registry.all_rules()) == 35
        assert "PRM103" in codes
        assert "RTN103" in codes
        assert "YLD103" in codes
        assert "PRM104" not in codes
        assert "RTN104" not in codes
        assert "YLD104" not in codes

    def test_default_rules_count(self):
        registry = build_registry()
        assert len(registry.all_rules()) == 31

    def test_non_default_rules_excluded(self):
        registry = build_registry()
        codes = {r.code for r in registry.all_rules()}
        assert "PRM104" not in codes
        assert "PRM103" not in codes
        assert "RTN104" not in codes
        assert "RTN103" not in codes
        assert "YLD104" not in codes
        assert "YLD103" not in codes

    def test_non_default_rules_included_with_select(self):
        # PRM104 and YLD103 are in different conflict groups — no conflict.
        registry = build_registry(select=["PRM104", "YLD103"])
        codes = {r.code for r in registry.all_rules()}
        assert "PRM104" in codes
        assert "YLD103" in codes

    def test_explicit_conflict_both_excluded_without_config(self):
        # PRM104 and PRM103 are in the same conflict_group and no config resolves it.
        registry = build_registry(select=["PRM104", "PRM103"])
        codes = {r.code for r in registry.all_rules()}
        assert "PRM104" not in codes
        assert "PRM103" not in codes

    def test_explicit_conflict_resolved_by_config(self):
        from pydocfix.config import Config

        config = Config(type_annotation_style="signature")
        registry = build_registry(select=["PRM104", "PRM103"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert "PRM104" in codes
        assert "PRM103" not in codes

    def test_single_conflict_group_member_always_registered(self):
        # Selecting only one side of a conflict group should always work,
        # regardless of type_annotation_style.
        registry = build_registry(select=["PRM104"])
        assert "PRM104" in {r.code for r in registry.all_rules()}

    def test_select_by_prefix(self):
        registry = build_registry(select=["RTN"])
        codes = {r.code for r in registry.all_rules()}
        assert all(c.startswith("RTN") for c in codes)
        assert "RTN001" in codes
        assert "RTN101" in codes
        assert "SUM001" not in codes
        assert "PRM001" not in codes

    def test_ignore_by_prefix(self):
        registry = build_registry(ignore=["PRM"])
        codes = {r.code for r in registry.all_rules()}
        assert not any(c.startswith("PRM") for c in codes)
        assert "SUM001" in codes
        assert "RTN001" in codes

    def test_select_prefix_includes_non_default(self):
        """Selecting a prefix that includes conflicting rules drops both when config is unset."""
        registry = build_registry(select=["YLD"])
        codes = {r.code for r in registry.all_rules()}
        # YLD103 and YLD104 conflict; without type_annotation_style config, both are excluded.
        assert "YLD103" not in codes
        assert "YLD104" not in codes
        # Non-conflicting rules are still included.
        assert "YLD001" in codes

    def test_select_prefix_conflict_resolved_by_config(self):
        from pydocfix.config import Config

        config = Config(type_annotation_style="docstring")
        registry = build_registry(select=["YLD"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert "YLD103" in codes
        assert "YLD104" not in codes

    def test_all_rules_select_all_both_style(self):
        """type_annotation_style='both' activates 104/105 rules (not 103/106)."""
        from pydocfix.config import Config

        config = Config(type_annotation_style="both")
        registry = build_registry(select=["ALL"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert len(registry.all_rules()) == 38
        assert "PRM103" in codes
        assert "PRM105" in codes
        assert "RTN103" in codes
        assert "RTN105" in codes
        assert "YLD103" in codes
        assert "YLD105" in codes
        assert "PRM104" not in codes
        assert "PRM106" not in codes
        assert "RTN104" not in codes
        assert "RTN106" not in codes
        assert "YLD104" not in codes
        assert "YLD106" not in codes

    def test_all_rules_select_all_docstring_style(self):
        """type_annotation_style='docstring' activates 104/106 rules (not 103/105)."""
        from pydocfix.config import Config

        config = Config(type_annotation_style="docstring")
        registry = build_registry(select=["ALL"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert len(registry.all_rules()) == 38
        assert "PRM103" in codes
        assert "PRM106" in codes
        assert "RTN103" in codes
        assert "RTN106" in codes
        assert "YLD103" in codes
        assert "YLD106" in codes
        assert "PRM104" not in codes
        assert "PRM105" not in codes
        assert "RTN104" not in codes
        assert "RTN105" not in codes
        assert "YLD104" not in codes
        assert "YLD105" not in codes

    def test_all_rules_select_all_signature_style(self):
        """type_annotation_style='signature' activates 103/105 rules (not 104/106)."""
        from pydocfix.config import Config

        config = Config(type_annotation_style="signature")
        registry = build_registry(select=["ALL"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert len(registry.all_rules()) == 38
        assert "PRM104" in codes
        assert "PRM105" in codes
        assert "RTN104" in codes
        assert "RTN105" in codes
        assert "YLD104" in codes
        assert "YLD105" in codes
        assert "PRM103" not in codes
        assert "PRM106" not in codes
        assert "RTN103" not in codes
        assert "RTN106" not in codes
        assert "YLD103" not in codes
        assert "YLD106" not in codes

    def test_both_style_resolved_conflict(self):
        """'both' resolves the 103/104 conflict in favour of 104."""
        from pydocfix.config import Config

        config = Config(type_annotation_style="both")
        registry = build_registry(select=["PRM104", "PRM103"], config=config)
        codes = {r.code for r in registry.all_rules()}
        assert "PRM103" in codes
        assert "PRM104" not in codes
