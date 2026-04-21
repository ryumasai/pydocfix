"""ANSI color helpers for pydocfix terminal output."""

from __future__ import annotations

from typing import Final

_RESET: Final[str] = "\033[0m"
_BOLD: Final[str] = "\033[1m"
_DIM: Final[str] = "\033[2m"
_RED: Final[str] = "\033[31m"
_GREEN: Final[str] = "\033[32m"
_BLUE: Final[str] = "\033[34m"


def ansi(text: str, *codes: str, color: bool = True) -> str:
    """Wrap *text* in ANSI escape codes if *color* is True."""
    if not color:
        return text
    return f"{''.join(codes)}{text}{_RESET}"
