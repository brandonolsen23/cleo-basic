"""Authentication helpers for RealTrack."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@dataclass
class RealTrackSession:
    """Manage a Playwright browser session backed by a storage state file."""

    storage_state_path: Path
    username: Optional[str] = None
    password: Optional[str] = None
    base_url: str = "https://www.realtrack.com"
    headless: bool = True

    _playwright: Optional[Any] = field(init=False, default=None)
    _browser: Optional[Browser] = field(init=False, default=None)
    _context: Optional[BrowserContext] = field(init=False, default=None)
    _search_page: Optional[Page] = field(init=False, default=None)

    async def __aenter__(self) -> "RealTrackSession":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        storage_state = None
        if self.storage_state_path.exists():
            storage_state = str(self.storage_state_path)
        self._context = await self._browser.new_context(storage_state=storage_state)
        self._search_page = await self._context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        if self._context is not None:
            await self._context.storage_state(path=str(self.storage_state_path))
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Playwright context not initialized")
        return self._context

    @property
    def search_page(self) -> Page:
        if self._search_page is None:
            raise RuntimeError("Search page not initialized")
        return self._search_page

    async def ensure_login(self) -> None:
        """Perform login if storage state is missing or credentials changed."""

        if await self._is_authenticated():
            return
        if not (self.username and self.password):
            raise RuntimeError("Missing credentials for RealTrack login.")
        await self._perform_login(self.username, self.password)
        await self.context.storage_state(path=str(self.storage_state_path))

    async def _is_authenticated(self) -> bool:
        """Check if the active session can access the search page."""

        page = self.search_page
        await page.goto(self.build_url("/?page=search"), wait_until="networkidle")
        html = await page.content()
        return "Logout" in html

    async def _perform_login(self, username: str, password: str) -> None:
        """Automate the RealTrack login form."""

        page = self.search_page
        await page.goto(self.build_url("/?page=login"), wait_until="networkidle")
        await page.fill('input[name="username"]', username)
        await page.fill('input[name="password"]', password)
        await page.click('input[name="function"][value="login"]')
        await page.wait_for_load_state("networkidle")
        html = await page.content()
        if "Logout" not in html:
            raise RuntimeError("RealTrack login failed; check credentials.")

    async def goto(self, path_or_url: str, *, wait_until: str = "networkidle") -> str:
        """Navigate the main search page to the provided path and return HTML."""

        page = self.search_page
        await page.goto(self._normalize_url(path_or_url), wait_until=wait_until)
        return await page.content()

    async def fetch(self, path_or_url: str, *, wait_until: str = "networkidle") -> str:
        """Open a transient page for detail views to keep search state intact."""

        page = await self.context.new_page()
        try:
            await page.goto(self._normalize_url(path_or_url), wait_until=wait_until)
            return await page.content()
        finally:
            await page.close()

    def _normalize_url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http"):
            return path_or_url
        base = self.base_url.rstrip("/")
        rel = path_or_url.lstrip("/")
        return f"{base}/{rel}"

    def build_url(self, path_or_url: str) -> str:
        """Public helper for other modules needing an absolute RealTrack URL."""

        return self._normalize_url(path_or_url)

    async def download_binary(self, path_or_url: str) -> bytes:
        """Fetch binary content using the browser context's request API."""

        url = self._normalize_url(path_or_url)
        last_error: Exception | None = None
        headers = {"Referer": self.base_url}
        for attempt in range(3):
            try:
                response = await self.context.request.get(url, headers=headers)
                if response.ok:
                    return await response.body()
                last_error = RuntimeError(
                    f"Asset download failed with status {response.status} for {url}"
                )
            except Exception as exc:  # pragma: no cover - network hiccups
                last_error = exc
            await asyncio.sleep(1)
        raise RuntimeError(f"Unable to download asset from {url}") from last_error
