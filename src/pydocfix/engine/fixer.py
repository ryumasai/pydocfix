"""Engine-internal fix application utilities."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from itertools import pairwise
from typing import Final

from pydocfix.diagnostics import Edit, Fix

logger = logging.getLogger(__name__)


def _fix_overlaps(accepted: list[Edit], candidate: Fix) -> bool:
    for new in candidate.edits:
        for existing in accepted:
            # Treat same-position pure insertions as overlapping so that
            # section-append edits are applied one per iteration, preventing
            # whitespace-only line artifacts between consecutive sections.
            if new.start == new.end == existing.start == existing.end:
                return True
            if new.start < existing.end and existing.start < new.end:
                return True
    return False


def apply_fixes(source: str, fixes: Iterable[Fix]) -> str:
    """Apply non-overlapping Fixes to a docstring.

    Fixes are accepted in iteration order; any Fix whose edits overlap with
    an already-accepted Fix is silently skipped.
    """
    accepted_edits: list[Edit] = []
    for fix in fixes:
        if _fix_overlaps(accepted_edits, fix):
            logger.warning("skipping fix due to overlapping edits")
            continue
        accepted_edits.extend(fix.edits)
    return apply_edits(source, accepted_edits)


def apply_edits(source: str, edits: Iterable[Edit]) -> str:
    """Apply Edits to a docstring, in reverse-offset order.

    Edit offsets are UTF-8 byte positions (as returned by pydocstring-rs).
    """
    sorted_edits: Final[list[Edit]] = sorted(edits, key=lambda e: e.start, reverse=True)
    # Validate no overlaps
    for prev, curr in pairwise(sorted_edits):
        if curr.end > prev.start:
            msg = f"Overlapping edits: [{curr.start}:{curr.end}] and [{prev.start}:{prev.end}]"
            raise ValueError(msg)
    buf: bytes = source.encode("utf-8")
    for edit in sorted_edits:
        buf = buf[: edit.start] + edit.new_text.encode("utf-8") + buf[edit.end :]
    return buf.decode("utf-8")
