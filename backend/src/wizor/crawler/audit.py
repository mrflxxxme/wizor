"""Оркестратор read-only краула сайта — единственная точка входа для backend (P2).

`audit_site` собирает guard'ированный HTTP-клиент (только GET, §6.1), обходит сайт до
`max_pages`, извлекает сигналы и факторы, валидирует JSON-LD и возвращает `CrawlResult`.

Инварианты фазы:
- **read-only (AC-7):** все сетевые запросы идут через `ReadOnlyGuard`; `read_only_confirmed`
  берётся из guard'а (ноль не-GET).
- **batch fault-isolation (AC-6):** per-page 4xx/5xx и сетевые сбои НЕ роняют батч — страница
  фиксируется (или пропускается с логом), обход продолжается.
- **SPA (AC-3):** JS-рендер через Playwright (см. `fetch`), флаг `rendered_via_js`.

Тестируемость: `transport`/`render`/адаптеры инъектируются (keyword-only, с дефолтами) —
юнит-тесты подают `httpx.MockTransport` и fake-render, не выходя в сеть. Публичная
сигнатура, которую вызывает backend, не меняется.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

import httpx
import structlog

from wizor.crawler import extractors
from wizor.crawler.adapters import (
    CoreWebVitalsAdapter,
    IndexabilityAdapter,
    StubCoreWebVitalsAdapter,
    StubIndexabilityAdapter,
)
from wizor.crawler.fetch import RenderFn, fetch_page, render_with_playwright
from wizor.crawler.guard import ReadOnlyGuard, build_guarded_client
from wizor.crawler.schemas import CrawlResult, FactorVerdict, PageAudit, SchemaValidation

logger = structlog.get_logger(__name__)


async def audit_site(
    site_url: str,
    *,
    max_pages: int = 100,
    timeout_s: int = 300,
    transport: httpx.AsyncBaseTransport | None = None,
    render: RenderFn | None = render_with_playwright,
    cwv_adapter: CoreWebVitalsAdapter | None = None,
    indexability_adapter: IndexabilityAdapter | None = None,
) -> CrawlResult:
    """Провести read-only аудит сайта и вернуть структурированный `CrawlResult`.

    Никогда не поднимает исключение на per-page ошибке (AC-6). Полный провал (недоступна
    стартовая страница) → `CrawlResult.error` заполнен, `pages` пуст.
    """
    cwv_adapter = cwv_adapter or StubCoreWebVitalsAdapter()
    indexability_adapter = indexability_adapter or StubIndexabilityAdapter()
    # На страницу — доля общего бюджета; минимум 5с, чтобы Playwright успел рендер.
    per_page_timeout_s = max(5.0, timeout_s / max(1, max_pages))

    guard = ReadOnlyGuard()
    crawled_at = datetime.now(UTC)
    client = build_guarded_client(guard, inner=transport, timeout_s=per_page_timeout_s)
    # Штатный Playwright-рендер связываем с ЭТИМ guard'ом, чтобы browser-трафик (route-abort
    # не-GET) фиксировался в том же журнале и попадал в read_only_confirmed (F1/AC-7).
    active_render = _bind_render_guard(render, guard)
    try:
        pages, page_signals = await _crawl_pages(
            site_url,
            client=client,
            max_pages=max_pages,
            per_page_timeout_s=per_page_timeout_s,
            render=active_render,
        )
        if not pages:
            return CrawlResult(
                site_url=site_url,
                crawled_at=crawled_at,
                pages=[],
                audit_summary=[],
                schema_validation=SchemaValidation(schema_valid=True),
                read_only_confirmed=guard.confirmed_read_only,
                error="стартовая страница недоступна — краул не выполнен",
            )
        robots_txt = await _fetch_text(client, urljoin(site_url, "/robots.txt"))
        sitemap_present = await _probe_sitemap(client, site_url)
        audit_summary = await _build_summary(
            site_url,
            pages=pages,
            page_signals=page_signals,
            robots_txt=robots_txt,
            sitemap_present=sitemap_present,
            cwv_adapter=cwv_adapter,
            indexability_adapter=indexability_adapter,
        )
        schema_validation = _validate_schema(page_signals)
    finally:
        await client.aclose()

    return CrawlResult(
        site_url=site_url,
        crawled_at=crawled_at,
        pages=pages,
        audit_summary=audit_summary,
        schema_validation=schema_validation,
        read_only_confirmed=guard.confirmed_read_only,
        error=None,
    )


def _bind_render_guard(render: RenderFn | None, guard: ReadOnlyGuard) -> RenderFn | None:
    """Связать штатный Playwright-рендер с guard'ом (browser route-abort пишет в тот же журнал).

    Кастомный/подменённый render (тесты) остаётся как есть — не оборачиваем.
    """
    if render is not render_with_playwright:
        return render

    async def _guarded_render(url: str, timeout_ms: int) -> str | None:
        return await render_with_playwright(url, timeout_ms, guard=guard)

    return _guarded_render


async def _crawl_pages(
    site_url: str,
    *,
    client: httpx.AsyncClient,
    max_pages: int,
    per_page_timeout_s: float,
    render: RenderFn | None,
) -> tuple[list[PageAudit], list[dict[str, object]]]:
    """Обойти сайт вширь от стартового URL; собрать `PageAudit` + сигналы страниц (AC-6)."""
    queue: list[str] = [site_url]
    seen: set[str] = {site_url}
    base_host = urlparse(site_url).netloc
    pages: list[PageAudit] = []
    page_signals: list[dict[str, object]] = []

    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        try:
            fetched = await fetch_page(
                url, client=client, timeout_s=per_page_timeout_s, render=render
            )
        except httpx.HTTPError as exc:
            # Сетевой сбой одной страницы не роняет батч (AC-6) — логируем и идём дальше.
            logger.warning("crawler.page_fetch_failed", url=url, error=str(exc))
            continue

        signals = extractors.extract_page_signals(fetched.html)
        pages.append(
            PageAudit(
                url=fetched.url,
                http_status=fetched.http_status,
                content_hash=fetched.content_hash,
                rendered_via_js=fetched.rendered_via_js,
                signals=signals,
            )
        )
        page_signals.append(signals)

        # Ссылки для дальнейшего обхода берём только с успешных (2xx) страниц.
        if 200 <= fetched.http_status < 300:
            for link in extractors.discover_links(fetched.html, url):
                if link not in seen and urlparse(link).netloc == base_host:
                    seen.add(link)
                    queue.append(link)

    return pages, page_signals


async def _build_summary(
    site_url: str,
    *,
    pages: list[PageAudit],
    page_signals: list[dict[str, object]],
    robots_txt: str | None,
    sitemap_present: bool,
    cwv_adapter: CoreWebVitalsAdapter,
    indexability_adapter: IndexabilityAdapter,
) -> list[FactorVerdict]:
    """Собрать вердикты по всем аудит-факторам (AC-2)."""
    statuses = [p.http_status for p in pages]
    return [
        extractors.robots_verdict(robots_txt),
        extractors.sitemap_verdict(sitemap_present),
        extractors.http_status_verdict(statuses),
        extractors.html_semantics_verdict(page_signals),
        extractors.json_ld_verdict(page_signals),
        extractors.faq_verdict(page_signals),
        await cwv_adapter.evaluate(site_url),
        await indexability_adapter.evaluate(site_url),
    ]


def _validate_schema(page_signals: list[dict[str, object]]) -> SchemaValidation:
    """Провалидировать все JSON-LD блоки со всех страниц (AC-4)."""
    from wizor.crawler.schema_validator import validate_json_ld

    blocks: list[str] = []
    for signal in page_signals:
        raw = signal.get("json_ld_blocks")
        if isinstance(raw, list):
            blocks.extend(str(b) for b in raw)
    return validate_json_ld(blocks)


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    """GET-запрос текста; None при недоступности (fault-isolated)."""
    try:
        response = await client.get(url)
    except httpx.HTTPError:
        return None
    if 200 <= response.status_code < 300:
        return response.text
    return None


async def _probe_sitemap(client: httpx.AsyncClient, site_url: str) -> bool:
    """Проверить наличие /sitemap.xml (best-effort GET)."""
    text = await _fetch_text(client, urljoin(site_url, "/sitemap.xml"))
    if text is None:
        return False
    return "<urlset" in text or "<sitemapindex" in text
