"""Shared fixtures for engine tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def load_test_fixture():
    """Return a callable that resolves paths within engine/fixtures/."""

    def _load(name: str) -> Path:
        return Path(__file__).parent / "fixtures" / name

    return _load


@pytest.fixture
def install_fixture(load_test_fixture):
    """Return a callable that copies a fixture file into a target directory."""

    def _install(name: str, dest: Path, *, filename: str | None = None) -> Path:
        src = load_test_fixture(name)
        target = dest / (filename or src.name)
        shutil.copy(src, target)
        return target

    return _install


@pytest.fixture
def runner():
    """Return a Click test runner."""
    return CliRunner()
