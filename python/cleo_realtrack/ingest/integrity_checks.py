"""Safety checks for the RealTrack ingest workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Set


def verify_html_vs_state(html_dir: Path, seen_rt_ids: Iterable[str]) -> None:
    """Ensure there is a one-to-one relationship between files and seen IDs."""

    files = list(html_dir.glob("RT*.html"))
    id_count = len(set(seen_rt_ids))
    if len(files) != id_count:
        raise RuntimeError(
            "Mismatch between saved HTML files and seen_rt_ids count"
        )


def verify_total_count_bounds(total_count: int, seen_rt_ids: Set[str]) -> None:
    """Validate RealTrack total count invariants."""

    if len(seen_rt_ids) < 200:
        return
    if len(seen_rt_ids) > total_count:
        raise RuntimeError("seen_rt_ids exceeds RealTrack total count")
    if total_count - len(seen_rt_ids) > 100:
        raise RuntimeError(
            "Unexpectedly large backlog suggests UI or search parameters changed"
        )


def verify_known_rt_encounter(found_known: bool) -> None:
    """Assert that at least one known RT ID appeared within skip <= 3."""

    if not found_known:
        raise RuntimeError(
            "Ordering invariant broken: expected to find known RT by skip<=3"
        )
