"""GET-only загрузка страниц + Playwright JS-рендер для SPA (AC-3).

Слой доступа к сети краула. Статический HTML берётся guarded httpx-клиентом (только
GET, §6.1). Для SPA дополнительно выполняется JS-рендер headless-Chromium (Playwright).

Read-only в браузере enforce'ится структурно: ДО `page.goto` регистрируется route-хендлер
`page.route("**/*", …)`, который на КАЖДЫЙ browser-запрос (навигация, XHR/fetch/beacon,
сабресурсы) пишет метод в общий `ReadOnlyGuard` и рвёт любой не-GET через `route.abort()`
на уровне Chromium. Поэтому JS страницы не может выпустить POST/PUT/… мимо guard'а, а
`read_only_confirmed` покрывает и browser-трафик. Итог по странице: HTTP-статус, финальный
HTML, `content_hash` и флаг `rendered_via_js` (изменил ли JS-рендер контент — признак SPA).

Playwright запускается под предустановленным Chromium (env
`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`); `playwright install` не запускается.
Рендер вынесен за интерфейс `RenderFn`, чтобы юнит-тесты подменяли его без сети/браузера.
"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from wizor.crawler.guard import ReadOnlyGuard

# Тип функции JS-рендера: url + таймаут(мс) → отрендеренный HTML или None (провал).
RenderFn = Callable[[str, int], Awaitable[str | None]]

# Признаки SPA-каркаса: если сырой HTML их содержит, JS-рендер оправдан.
_SPA_HINTS = ("__NEXT_DATA__", "ng-app", "data-reactroot", 'id="root"', 'id="app"', "v-app")


@dataclass(frozen=True)
class FetchedPage:
    """Результат загрузки одной страницы."""

    url: str
    http_status: int
    html: str
    """Финальный HTML (после JS-рендера, если он применялся)."""
    content_hash: str
    """sha256 нормализованного финального HTML — основа P8 re-crawl delta."""
    rendered_via_js: bool
    """True, если JS-рендер изменил нормализованный контент (SPA, AC-3)."""


def normalize_html(html: str) -> str:
    """Нормализовать HTML к стабильному текстовому представлению для хеша/сравнения.

    Скрипты и стили выкидываются, видимый текст схлопывается по пробелам. Это делает
    `content_hash` устойчивым к незначимому шуму и позволяет детектить SPA-рендер
    (сырой каркас без контента vs отрендеренная страница с контентом дают разный хеш).
    """
    soup = BeautifulSoup(html or "", "lxml")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def content_hash(html: str) -> str:
    """sha256 нормализованного HTML (hex)."""
    return hashlib.sha256(normalize_html(html).encode("utf-8")).hexdigest()


def _looks_like_spa(raw_html: str) -> bool:
    """Эвристика: похоже ли на SPA-каркас (стоит ли гонять JS-рендер)."""
    return any(hint in raw_html for hint in _SPA_HINTS)


def make_route_guard(guard: ReadOnlyGuard | None) -> Callable[[Any], Awaitable[None]]:
    """Собрать Playwright route-хендлер: пишет метод в guard и рвёт любой не-GET.

    Каждый browser-запрос (навигация/XHR/fetch/beacon/сабресурс) фиксируется в `guard`
    (если задан) через `guard.record`, затем GET продолжается (`route.continue_`), а любой
    не-GET физически прерывается на уровне Chromium (`route.abort`) — write наружу не уходит.
    """

    async def _handler(route: Any) -> None:
        request = route.request
        method: str = request.method
        if guard is not None:
            guard.record(method, request.url)
        if method.upper() == "GET":
            await route.continue_()
        else:
            await route.abort()

    return _handler


async def render_with_playwright(
    url: str, timeout_ms: int, *, guard: ReadOnlyGuard | None = None
) -> str | None:
    """Отрендерить страницу headless-Chromium и вернуть HTML после JS (browser GET-only).

    ДО навигации ставится route-хендлер (см. `make_route_guard`): GET проходит, любой не-GET
    из JS страницы рвётся на уровне Chromium и фиксируется в `guard`. Навигация — HTTP GET
    (`page.goto`). При любой ошибке возвращает None (fallback на статический HTML, self-audit
    пометит `spa_render: failed`).
    """
    # Импорт локальный: Playwright не нужен, если рендер отключён/подменён в тестах.
    from playwright.async_api import async_playwright

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                # Route-хендлер регистрируется ДО goto — иначе первые запросы уйдут мимо guard.
                await page.route("**/*", make_route_guard(guard))
                await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                return await page.content()
            finally:
                await browser.close()
    except Exception:
        return None


async def fetch_page(
    url: str,
    *,
    client: httpx.AsyncClient,
    timeout_s: float,
    render: RenderFn | None = render_with_playwright,
) -> FetchedPage:
    """Загрузить страницу: статический GET + (при необходимости) JS-рендер.

    Per-page HTTP-ошибки (4xx/5xx) НЕ поднимаются — статус попадает в результат, батч
    продолжается (AC-6). Сетевой сбой пробрасывается вызывающему (оркестратор audit
    ловит его пофайлово).
    """
    response = await client.get(url)
    raw_html = response.text
    final_html = raw_html
    rendered_via_js = False

    if render is not None and _looks_like_spa(raw_html):
        rendered = await render(url, int(timeout_s * 1000))
        if rendered is not None and normalize_html(rendered) != normalize_html(raw_html):
            final_html = rendered
            rendered_via_js = True

    return FetchedPage(
        url=url,
        http_status=response.status_code,
        html=final_html,
        content_hash=content_hash(final_html),
        rendered_via_js=rendered_via_js,
    )
