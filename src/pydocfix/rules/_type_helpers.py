"""Shared type-normalisation helpers used by type-mismatch rules."""

from __future__ import annotations

import ast


def normalize_optional(type_str: str) -> str:
    """Strip ``Optional[T]`` / ``T | None`` / ``Union[T, None]`` to ``T``.

    Handles:
    - ``Optional[T]``            → ``T``
    - ``T | None`` / ``None | T`` → ``T``
    - ``Union[T, None]``         → ``T``
    - ``Union[T, S, None]``      → ``Union[T, S]``

    All other forms are returned unchanged.  On ``SyntaxError`` the original
    string is returned verbatim.
    """
    try:
        node = ast.parse(type_str, mode="eval").body
    except SyntaxError:
        return type_str

    result = _strip_none(node)
    return ast.unparse(result) if result is not node else type_str


def _strip_none(node: ast.expr) -> ast.expr:
    """Return node with a single ``None`` member removed, or the original node."""
    # Optional[T]
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "Optional":
        return node.slice  # type: ignore[return-value]

    # T | None  /  None | T
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = node.left, node.right
        if _is_none_const(right):
            return left
        if _is_none_const(left):
            return right

    # Union[T, None]  /  Union[T, S, None]
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Union"
        and isinstance(node.slice, ast.Tuple)
    ):
        elts = node.slice.elts
        non_none = [e for e in elts if not _is_none_const(e)]
        if len(non_none) == len(elts) - 1:
            if len(non_none) == 1:
                return non_none[0]
            new_slice = ast.Tuple(elts=non_none, ctx=ast.Load())
            return ast.Subscript(
                value=ast.Name(id="Union", ctx=ast.Load()),
                slice=new_slice,
                ctx=ast.Load(),
            )

    return node


def _is_none_const(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None
