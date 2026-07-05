"""Unit: оркестратор audit_site — SPA-рендер (AC-3), fault-isolation (AC-6), read-only.

Сеть не используется: `httpx.MockTransport` обслуживает фейковый сайт, JS-рендер
подменён fake-функцией. Playwright/Chromium в юнит-слое не запускается.
"""

from __future__ import annotations

import httpx
import pytest

from wizor.crawler.audit import audit_site

_BASE = "https://test-site.ru"

# Стартовая страница — SPA-каркас: id="root", БЕЗ <h1> в сыром HTML (AC-3).
_HOME_RAW = """
<html><head><title>Home</title></head>
<body><div id="root"></div>
<a href="/about">about</a><a href="/broken">broken</a></body></html>
"""

# Тот же URL после JS-рендера — контент появился, есть <h1>.
_HOME_RENDERED = """
<html><head><title>Home</title></head>
<body><div id="root"><main><h1>Главная после рендера</h1>
<article>контент</article></main></div>
<a href="/about">about</a><a href="/broken">broken</a></body></html>
"""

_ABOUT = """
<html><body><main><article><h1>О компании</h1>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","name":"Acme"}
</script></article></main></body></html>
"""

_ROBOTS = "User-agent: GPTBot\nAllow: /\nSitemap: https://test-site.ru/sitemap.xml"
_SITEMAP = '<?xml version="1.0"?><urlset><url><loc>https://test-site.ru/about</loc></url></urlset>'


def _fake_site_transport() -> httpx.MockTransport:
    """MockTransport, отдающий фейковый сайт; /broken → 404 (для AC-6)."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in ("", "/"):
            return httpx.Response(200, text=_HOME_RAW, headers={"content-type": "text/html"})
        if path == "/about":
            return httpx.Response(200, text=_ABOUT, headers={"content-type": "text/html"})
        if path == "/broken":
            return httpx.Response(404, text="not found")
        if path == "/robots.txt":
            return httpx.Response(200, text=_ROBOTS)
        if path == "/sitemap.xml":
            return httpx.Response(200, text=_SITEMAP)
        return httpx.Response(404, text="nope")

    return httpx.MockTransport(handler)


async def _fake_render(url: str, timeout_ms: int) -> str | None:
    """Fake JS-рендер: для главной возвращает отрендеренный HTML, иначе None."""
    if url.rstrip("/") == _BASE:
        return _HOME_RENDERED
    return None


@pytest.mark.asyncio
async def test_audit_spa_render_extracts_h1() -> None:
    """AC-3: SPA — <h1> найден после JS-рендера, флаг rendered_via_js выставлен."""
    result = await audit_site(
        _BASE, max_pages=10, timeout_s=30, transport=_fake_site_transport(), render=_fake_render
    )
    home = next(p for p in result.pages if p.url.rstrip("/") == _BASE)
    assert home.rendered_via_js is True
    assert home.signals["h1"] == ["Главная после рендера"]


@pytest.mark.asyncio
async def test_audit_batch_fault_isolation() -> None:
    """AC-6: страница 404 не роняет батч — остальные обработаны."""
    result = await audit_site(
        _BASE, max_pages=10, timeout_s=30, transport=_fake_site_transport(), render=_fake_render
    )
    statuses = {p.http_status for p in result.pages}
    urls = {p.url for p in result.pages}
    assert 404 in statuses
    assert f"{_BASE}/about" in urls  # соседняя обработана несмотря на 404
    assert result.error is None


@pytest.mark.asyncio
async def test_audit_read_only_confirmed() -> None:
    """AC-7: краул подтверждает read-only (guard не зафиксировал не-GET)."""
    result = await audit_site(
        _BASE, max_pages=10, timeout_s=30, transport=_fake_site_transport(), render=_fake_render
    )
    assert result.read_only_confirmed is True


@pytest.mark.asyncio
async def test_audit_summary_all_factors_present() -> None:
    """AC-2: по каждому фактору есть вердикт; CWV/индексируемость — deferred (stub)."""
    result = await audit_site(
        _BASE, max_pages=10, timeout_s=30, transport=_fake_site_transport(), render=_fake_render
    )
    factors = {v.factor: v.verdict for v in result.audit_summary}
    assert set(factors) == {
        "robots_txt",
        "sitemap",
        "http_status",
        "html_semantics",
        "json_ld",
        "faq",
        "cwv",
        "indexability",
    }
    assert factors["robots_txt"] == "pass"  # GPTBot разрешён
    assert factors["sitemap"] == "pass"
    assert factors["cwv"] == "deferred"
    assert factors["indexability"] == "deferred"


@pytest.mark.asyncio
async def test_audit_schema_validation_from_pages() -> None:
    """AC-4: JSON-LD со страниц провалидирован (валидный Organization)."""
    result = await audit_site(
        _BASE, max_pages=10, timeout_s=30, transport=_fake_site_transport(), render=_fake_render
    )
    assert result.schema_validation.schema_valid is True
    assert "Organization" in result.schema_validation.types_found


@pytest.mark.asyncio
async def test_audit_unreachable_site_sets_error() -> None:
    """Полный провал (стартовая страница недоступна) → error заполнен, pages пуст."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable")

    result = await audit_site(
        _BASE, max_pages=5, timeout_s=10, transport=httpx.MockTransport(handler), render=None
    )
    assert result.pages == []
    assert result.error is not None
    assert result.read_only_confirmed is True
