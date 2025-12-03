"""Ingest layer modules for interacting with RealTrack."""

from .login import RealTrackSession
from .search_nav import (
    DEFAULT_SEARCH_CONFIG,
    SearchConfig,
    open_saved_search,
    prepare_saved_search,
)
from .extract_links import extract_detail_links, ensure_absolute
from .extract_rt_id import extract_rt_id
from .integrity_checks import (
    verify_html_vs_state,
    verify_total_count_bounds,
    verify_known_rt_encounter,
)
from .search_page import extract_total_count
from .assets import download_transaction_assets

__all__ = [
    "RealTrackSession",
    "open_saved_search",
    "prepare_saved_search",
    "SearchConfig",
    "DEFAULT_SEARCH_CONFIG",
    "ensure_absolute",
    "extract_detail_links",
    "extract_rt_id",
    "verify_html_vs_state",
    "verify_total_count_bounds",
    "verify_known_rt_encounter",
    "extract_total_count",
    "download_transaction_assets",
]
