"""Tests for linting rules and rule infrastructure."""

from __future__ import annotations

import ast
from pathlib import Path

from pydocstring import Node, SyntaxKind, Token, parse_google, parse_numpy

from pydocfix.rules import (
    D200,
    D401,
    DiagnoseContext,
    Diagnostic,
    Edit,
    Fix,
    Range,
    apply_edits,
    build_registry,
)


def _make_diagnose_ctx(raw: str) -> DiagnoseContext:
    """Create a DiagnoseContext with the SUMMARY token as cst_node."""
    parsed = parse_google(raw)
    model = parsed.to_model()
    # Find the SUMMARY token in the CST
    summary_token = parsed.summary
    if summary_token is None:
        # Create a dummy token for empty docstrings
        summary_token = Token(kind="SUMMARY", text="", start=0, end=0)
    return DiagnoseContext(
        filepath=Path("test.py"),
        docstring_source=raw,
        docstring_model=model,
        cst=parsed,
        cst_node=summary_token,
        ast_node=ast.parse("pass").body[0],
        range=Range(start_line=1, start_col=0, end_line=1, end_col=len(raw)),
        indent=0,
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
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestDiagnostic:
    def test_fixable_when_fix_present(self):
        d = Diagnostic(
            rule="D200",
            message="test",
            filepath="test.py",
            range=Range(1, 0, 1, 10),
            fix=Fix(edits=[]),
        )
        assert d.fixable is True

    def test_not_fixable_when_no_fix(self):
        d = Diagnostic(
            rule="D200",
            message="test",
            filepath="test.py",
            range=Range(1, 0, 1, 10),
        )
        assert d.fixable is False

    def test_line_and_col_properties(self):
        d = Diagnostic(
            rule="D200",
            message="test",
            filepath="test.py",
            range=Range(start_line=5, start_col=4, end_line=7, end_col=0),
        )
        assert d.line == 5
        assert d.col == 4


class TestD200:
    def test_missing_period(self):
        ctx = _make_diagnose_ctx("Do something")
        diag = D200().diagnose(ctx)
        assert diag is not None
        assert diag.rule == "D200"
        assert diag.fixable is True
        assert diag.fix is not None

    def test_has_period(self):
        ctx = _make_diagnose_ctx("Do something.")
        diag = D200().diagnose(ctx)
        assert diag is None

    def test_empty_summary(self):
        # Empty docstrings have no SUMMARY token in the CST,
        # so D200 is never dispatched. Tested via checker integration.
        pass

    def test_fix_returns_edit(self):
        raw = "Do something"
        ctx = _make_diagnose_ctx(raw)
        diag = D200().diagnose(ctx)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(raw, diag.fix.edits)
        assert result == "Do something."

    def test_fix_no_change_when_period_exists(self):
        raw = "Do something."
        ctx = _make_diagnose_ctx(raw)
        diag = D200().diagnose(ctx)
        assert diag is None

    def test_fix_preserves_surrounding_text(self):
        raw = "Do something\n\n    Args:\n        x: val.\n"
        ctx = _make_diagnose_ctx(raw)
        diag = D200().diagnose(ctx)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(raw, diag.fix.edits)
        assert "Do something." in result
        assert "    Args:\n        x: val.\n" in result


class TestRegistry:
    def test_build_registry_contains_d200(self):
        registry = build_registry()
        assert registry.get("D200") is not None

    def test_build_registry_contains_d401(self):
        registry = build_registry()
        assert registry.get("D401") is not None

    def test_all_rules(self):
        registry = build_registry()
        rules = registry.all_rules()
        codes = [r.code for r in rules]
        assert "D200" in codes
        assert "D401" in codes

    def test_rules_for_kind(self):
        registry = build_registry()
        summary_rules = registry.rules_for_kind(SyntaxKind.SUMMARY)
        assert any(r.code == "D200" for r in summary_rules)
        assert registry.rules_for_kind(SyntaxKind.COLON) == []
        google_arg_rules = registry.rules_for_kind(SyntaxKind.GOOGLE_ARG)
        assert any(r.code == "D401" for r in google_arg_rules)


# ── Helpers for D401 ─────────────────────────────────────────────────


def _make_d401_ctx_google(
    ds_text: str,
    func_src: str,
    cst_node: Node | Token,
) -> DiagnoseContext:
    """Build a DiagnoseContext for D401 tests (Google style)."""
    parsed = parse_google(ds_text)
    model = parsed.to_model()
    tree = ast.parse(func_src)
    func_node = tree.body[0]
    return DiagnoseContext(
        filepath=Path("test.py"),
        docstring_source=ds_text,
        docstring_model=model,
        cst=parsed,
        cst_node=cst_node,
        ast_node=func_node,
        range=Range(start_line=2, start_col=4, end_line=6, end_col=4),
        indent=4,
    )


def _find_cst_nodes(parsed, kind: SyntaxKind) -> list[Node]:
    """Find all CST nodes of a given kind."""
    results: list[Node] = []

    def _walk(n):
        if hasattr(n, "children"):
            if n.kind == kind:
                results.append(n)
            for c in n.children:
                _walk(c)
        elif isinstance(n, Token) and n.kind == kind:
            results.append(n)

    _walk(parsed.node)
    return results


# ── D401 Tests ───────────────────────────────────────────────────────


class TestD401GoogleParam:
    """D401: parameter type mismatch in Google-style docstrings."""

    def test_mismatch_detected(self):
        ds = "Summary.\n\nArgs:\n    x (str): The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        assert len(args) == 1
        ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = D401().diagnose(ctx)
        assert diag is not None
        assert diag.rule == "D401"
        assert "'str'" in diag.message
        assert "'int'" in diag.message
        assert "'x'" in diag.message

    def test_matching_types_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (int): The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = D401().diagnose(ctx)
        assert diag is None

    def test_no_annotation_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x (str): The x value.\n"
        func = "def foo(x):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = D401().diagnose(ctx)
        assert diag is None

    def test_no_doc_type_no_diagnostic(self):
        ds = "Summary.\n\nArgs:\n    x: The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = D401().diagnose(ctx)
        assert diag is None

    def test_fix_replaces_type(self):
        ds = "Summary.\n\nArgs:\n    x (str): The x value.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = D401().diagnose(ctx)
        assert diag is not None
        assert diag.fix is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "(int)" in result

    def test_complex_type(self):
        ds = "Summary.\n\nArgs:\n    items (list): The items.\n"
        func = "def foo(items: list[int]):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        ctx = _make_d401_ctx_google(ds, func, args[0])
        diag = D401().diagnose(ctx)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "(list[int])" in result

    def test_multiple_params(self):
        ds = "Summary.\n\nArgs:\n    x (str): X.\n    y (int): Y.\n"
        func = "def foo(x: int, y: int):\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        assert len(args) == 2
        # x: str vs int → mismatch
        ctx0 = _make_d401_ctx_google(ds, func, args[0])
        diag0 = D401().diagnose(ctx0)
        assert diag0 is not None
        assert "'x'" in diag0.message
        # y: int vs int → match
        ctx1 = _make_d401_ctx_google(ds, func, args[1])
        diag1 = D401().diagnose(ctx1)
        assert diag1 is None

    def test_class_method_skipped(self):
        """Non-function AST nodes (e.g. class) should not crash."""
        ds = "Summary.\n\nArgs:\n    x (int): X.\n"
        func = "class Foo:\n    pass\n"
        parsed = parse_google(ds)
        args = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_ARG)
        tree = ast.parse(func)
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_source=ds,
            docstring_model=parsed.to_model(),
            cst=parsed,
            cst_node=args[0],
            ast_node=tree.body[0],
            range=Range(start_line=1, start_col=0, end_line=1, end_col=0),
            indent=0,
        )
        diag = D401().diagnose(ctx)
        assert diag is None


class TestD401GoogleReturn:
    """D401: return type mismatch in Google-style docstrings."""

    def test_mismatch_detected(self):
        ds = "Summary.\n\nReturns:\n    str: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_RETURNS)
        assert len(rets) == 1
        ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = D401().diagnose(ctx)
        assert diag is not None
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_matching_return_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_RETURNS)
        ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = D401().diagnose(ctx)
        assert diag is None

    def test_no_return_annotation_no_diagnostic(self):
        ds = "Summary.\n\nReturns:\n    int: The result.\n"
        func = "def foo():\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_RETURNS)
        ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = D401().diagnose(ctx)
        assert diag is None

    def test_fix_replaces_return_type(self):
        ds = "Summary.\n\nReturns:\n    str: The result.\n"
        func = "def foo() -> bool:\n    pass\n"
        parsed = parse_google(ds)
        rets = _find_cst_nodes(parsed, SyntaxKind.GOOGLE_RETURNS)
        ctx = _make_d401_ctx_google(ds, func, rets[0])
        diag = D401().diagnose(ctx)
        assert diag is not None
        result = apply_edits(ds, diag.fix.edits)
        assert "bool:" in result


class TestD401Numpy:
    """D401: type mismatch in NumPy-style docstrings."""

    def test_param_mismatch(self):
        ds = "Summary.\n\nParameters\n----------\nx : str\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, SyntaxKind.NUMPY_PARAMETER)
        assert len(params) == 1
        model = parsed.to_model()
        tree = ast.parse(func)
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_source=ds,
            docstring_model=model,
            cst=parsed,
            cst_node=params[0],
            ast_node=tree.body[0],
            range=Range(start_line=2, start_col=4, end_line=8, end_col=4),
            indent=4,
        )
        diag = D401().diagnose(ctx)
        assert diag is not None
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_return_mismatch(self):
        ds = "Summary.\n\nReturns\n-------\nstr\n    The result.\n"
        func = "def foo() -> int:\n    pass\n"
        parsed = parse_numpy(ds)
        rets = _find_cst_nodes(parsed, SyntaxKind.NUMPY_RETURNS)
        assert len(rets) == 1
        model = parsed.to_model()
        tree = ast.parse(func)
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_source=ds,
            docstring_model=model,
            cst=parsed,
            cst_node=rets[0],
            ast_node=tree.body[0],
            range=Range(start_line=2, start_col=4, end_line=8, end_col=4),
            indent=4,
        )
        diag = D401().diagnose(ctx)
        assert diag is not None
        assert "'str'" in diag.message
        assert "'int'" in diag.message

    def test_param_match_no_diagnostic(self):
        ds = "Summary.\n\nParameters\n----------\nx : int\n    The x.\n"
        func = "def foo(x: int):\n    pass\n"
        parsed = parse_numpy(ds)
        params = _find_cst_nodes(parsed, SyntaxKind.NUMPY_PARAMETER)
        model = parsed.to_model()
        tree = ast.parse(func)
        ctx = DiagnoseContext(
            filepath=Path("test.py"),
            docstring_source=ds,
            docstring_model=model,
            cst=parsed,
            cst_node=params[0],
            ast_node=tree.body[0],
            range=Range(start_line=2, start_col=4, end_line=8, end_col=4),
            indent=4,
        )
        diag = D401().diagnose(ctx)
        assert diag is None
