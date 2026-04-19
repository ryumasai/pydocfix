"""Shared fixtures for engine tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pydocfix.diagnostics import Diagnostic, Fix, Offset, Range


@pytest.fixture
def load_fixture():
    """Return a callable that loads a source file from fixtures/."""

    def _load(name: str) -> str:
        return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")

    return _load


@pytest.fixture
def make_diagnostic():
    """Return a factory for creating real Diagnostic objects (no mocks)."""

    def _make(rule: str, symbol: str = "", fix: Fix | None = None) -> Diagnostic:
        return Diagnostic(
            rule=rule,
            message="test diagnostic",
            filepath="test.py",
            range=Range(start=Offset(1, 1), end=Offset(1, 10)),
            symbol=symbol,
            fix=fix,
        )

    return _make
