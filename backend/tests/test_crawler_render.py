"""Unit: browser read-only enforcement (F1, AC-7) — Playwright route-abort не-GET.

Два уровня:
1. `make_route_guard` — чистый unit на фейковом Route (без браузера): не-GET рвётся
   (`route.abort`), метод пишется в guard.
2. Реальный headless-Chromium: страница с инлайновым `fetch(..., {method:'POST'})` —
   POST блокируется на уровне браузера И фиксируется в guard-журнале (сеть не задета,
   fetch прерван `route.abort`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from wizor.crawler.fetch import make_route_guard
from wizor.crawler.guard import ReadOnlyGuard


@dataclass
class _FakeRequest:
    method: str
    url: str


@dataclass
class _FakeRoute:
    """Мини-двойник Playwright Route: фиксирует continue_/abort."""

    request: _FakeRequest
    actions: list[str] = field(default_factory=list)

    async def continue_(self) -> None:
        self.actions.append("continue")

    async def abort(self) -> None:
        self.actions.append("abort")


@pytest.mark.asyncio
async def test_route_guard_allows_get() -> None:
    guard = ReadOnlyGuard()
    handler = make_route_guard(guard)
    route = _FakeRoute(_FakeRequest("GET", "https://site.ru/page"))
    await handler(route)
    assert route.actions == ["continue"]
    assert guard.confirmed_read_only is True
    assert [r.method for r in guard.records] == ["GET"]


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
@pytest.mark.asyncio
async def test_route_guard_aborts_non_get(method: str) -> None:
    guard = ReadOnlyGuard()
    handler = make_route_guard(guard)
    route = _FakeRoute(_FakeRequest(method, "https://site.ru/api"))
    await handler(route)
    # Не-GET физически прерван на уровне браузера И зафиксирован как нарушение.
    assert route.actions == ["abort"]
    assert guard.confirmed_read_only is False
    assert guard.violations[0].method == method


@pytest.mark.asyncio
async def test_route_guard_no_guard_still_aborts() -> None:
    """Без guard'а хендлер всё равно рвёт не-GET (structural), не падая."""
    handler = make_route_guard(None)
    route = _FakeRoute(_FakeRequest("POST", "https://site.ru/api"))
    await handler(route)
    assert route.actions == ["abort"]


def _chromium_available() -> bool:
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        return False
    return True


@pytest.mark.skipif(not _chromium_available(), reason="Playwright/Chromium недоступен")
@pytest.mark.asyncio
async def test_browser_blocks_and_records_fetch_post() -> None:
    """Реальный Chromium: JS-fetch POST страницы блокируется route-abort И пишется в guard.

    Страница задаётся локально (`set_content`, без навигации в сеть), инлайновый скрипт
    пытается `fetch(POST)`. Route-хендлер (тот же, что в render_with_playwright) рвёт его
    и фиксирует в guard — доказательство, что browser-путь покрыт AC-7 (F1).
    """
    from playwright.async_api import async_playwright

    guard = ReadOnlyGuard()
    html = (
        "<html><body>ok<script>"
        "fetch('https://blocked.example/collect',{method:'POST',body:'x'})"
        ".catch(()=>{});"
        "</script></body></html>"
    )
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.route("**/*", make_route_guard(guard))
                await page.set_content(html)
                # Дать событийному циклу выполнить fetch и пройти route-хендлер.
                for _ in range(40):
                    if any(r.method == "POST" for r in guard.records):
                        break
                    await page.wait_for_timeout(50)
            finally:
                await browser.close()
    except Exception as exc:  # окружение без sandbox → skip, не fail
        pytest.skip(f"Chromium не запустился в этом окружении: {exc}")

    post_records: list[Any] = [r for r in guard.records if r.method == "POST"]
    assert post_records, "browser POST не зафиксирован в guard (F1 не сработал)"
    assert all(not r.allowed for r in post_records)
    assert guard.confirmed_read_only is False
    assert any("blocked.example" in r.url for r in post_records)
