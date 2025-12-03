"""Navigate RealTrack's search UI and saved results pages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    from .login import RealTrackSession

SEARCH_FORM_PATH = "/?page=search"
RESULTS_PATH = "/?page=results"


@dataclass
class SearchConfig:
    """Parameters used to submit the RealTrack search form."""

    property_type: str = "retailBldg"
    per_page: str = "50"
    sort_primary: str = "regDate"
    sort_primary_order: str = "descending"
    sort_secondary: Optional[str] = None
    sort_secondary_order: str = "ascending"
    start_month: str = "1/1"
    start_year: str = "1996"
    end_month: str = "12/31"
    end_year: Optional[str] = None  # defaults to current year when unset

    def resolved_end_year(self) -> str:
        return self.end_year or str(date.today().year)


DEFAULT_SEARCH_CONFIG = SearchConfig()


async def prepare_saved_search(
    session: "RealTrackSession", config: SearchConfig = DEFAULT_SEARCH_CONFIG
) -> str:
    """Load the search form, apply filters, submit, and return the first results page."""

    page = session.search_page
    await page.goto(session.build_url(SEARCH_FORM_PATH), wait_until="networkidle")

    # Reset potentially sticky inputs before applying filters.
    await page.fill('input[name="sf2"]', "")
    await page.fill('input[name="sf4"]', "")
    await page.fill('input[name="sf7"]', "")
    await page.fill('input[name="sf8"]', "")

    await page.select_option('select[name="sf3"]', config.property_type)
    await page.select_option('select[name="sf9"]', config.per_page)
    await page.select_option('select[name="sort1"]', config.sort_primary)
    await page.select_option('select[name="order1"]', config.sort_primary_order)
    if config.sort_secondary:
        await page.select_option('select[name="sort2"]', config.sort_secondary)
        await page.select_option('select[name="order2"]', config.sort_secondary_order)

    await page.select_option('select[name="startmo"]', config.start_month)
    await page.select_option('select[name="startyr"]', config.start_year)
    await page.select_option('select[name="endmo"]', config.end_month)
    await page.select_option('select[name="endyr"]', config.resolved_end_year())

    await page.click('input[type="submit"][value="search"]')
    await page.wait_for_selector("#resultsTable")
    return await page.content()


async def open_saved_search(session: "RealTrackSession", *, page_index: int = 0) -> str:
    """Navigate to a RealTrack results page applying the provided page index."""

    delimiter = "&" if "?" in RESULTS_PATH else "?"
    path = f"{RESULTS_PATH}{delimiter}tabID={page_index}"
    return await session.goto(path)
