"""Извлечение аудит-факторов и сигналов страницы → `FactorVerdict` (AC-2).

Чистые функции разбора: HTML/robots/sitemap → структурные сигналы и вердикты
pass/warn/fail/deferred с RU-пояснением. Никакого I/O — легко тестируется фикстурами.

Пороговые правила здесь — разумные факт-уровневые дефолты (форк #6 PLAN). Веса и
итоговый Score — зона `geo-domain-expert` (P3); здесь только флаг по каждому фактору.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from wizor.crawler.schemas import FactorVerdict

# Семантические теги HTML5, наличие которых улучшает Comprehension-слой.
_SEMANTIC_TAGS: Final = ("article", "section", "nav", "aside", "header", "footer", "main")

# AI-краулеры, чьи разрешения в robots.txt важны для GEO-видимости.
_AI_BOTS: Final = ("GPTBot", "OAI-SearchBot", "PerplexityBot", "YandexBot", "Google-Extended")

# Маркеры FAQ / answer-first блоков (RU + EN + микроразметка).
_FAQ_PATTERNS: Final = (
    re.compile(r"\bFAQPage\b"),
    re.compile(r"часто задаваем", re.IGNORECASE),
    re.compile(r"\bF\.?A\.?Q\b", re.IGNORECASE),
    re.compile(r"вопрос[ы]?\s*[-—:]\s*ответ", re.IGNORECASE),
)


def extract_page_signals(html: str) -> dict[str, Any]:
    """Извлечь структурные сигналы страницы: h1–h3, семантические теги, JSON-LD, FAQ."""
    soup = BeautifulSoup(html or "", "lxml")
    headings = {
        level: [h.get_text(strip=True) for h in soup.find_all(level)]
        for level in ("h1", "h2", "h3")
    }
    semantic = [tag for tag in _SEMANTIC_TAGS if soup.find(tag) is not None]
    json_ld_blocks = [
        script.string or script.get_text()
        for script in soup.find_all("script", attrs={"type": "application/ld+json"})
    ]
    faq_hits = _detect_faq(html, json_ld_blocks)
    return {
        "h1": headings["h1"],
        "h2": headings["h2"],
        "h3": headings["h3"],
        "semantic_tags": semantic,
        "json_ld_blocks": json_ld_blocks,
        "faq_detected": faq_hits,
    }


def _detect_faq(html: str, json_ld_blocks: list[str]) -> bool:
    """Есть ли на странице FAQ / answer-first паттерн (в тексте или в JSON-LD)."""
    haystacks = [html or "", *json_ld_blocks]
    return any(pat.search(hay) for hay in haystacks for pat in _FAQ_PATTERNS)


def robots_verdict(robots_txt: str | None) -> FactorVerdict:
    """Вердикт по robots.txt: наличие + разрешения AI-ботам."""
    if robots_txt is None:
        return FactorVerdict(
            factor="robots_txt",
            verdict="warn",
            detail="robots.txt не найден — краулеры используют дефолтные правила; "
            "рекомендуется явно объявить доступ AI-ботам.",
            data={"present": False},
        )
    disallow_all = bool(re.search(r"(?im)^\s*disallow:\s*/\s*$", robots_txt))
    mentioned_bots = [bot for bot in _AI_BOTS if bot in robots_txt]
    if disallow_all:
        return FactorVerdict(
            factor="robots_txt",
            verdict="fail",
            detail="robots.txt запрещает обход всего сайта (Disallow: /) — "
            "AI-краулеры не смогут проиндексировать контент.",
            data={"present": True, "disallow_all": True, "ai_bots_mentioned": mentioned_bots},
        )
    verdict = "pass" if mentioned_bots else "warn"
    detail = (
        f"robots.txt найден; явно упомянуты AI-боты: {', '.join(mentioned_bots)}."
        if mentioned_bots
        else "robots.txt найден и не блокирует обход, но AI-боты не упомянуты явно — "
        "стоит добавить директивы для GPTBot/YandexBot и др."
    )
    return FactorVerdict(
        factor="robots_txt",
        verdict=verdict,
        detail=detail,
        data={"present": True, "disallow_all": False, "ai_bots_mentioned": mentioned_bots},
    )


def sitemap_verdict(sitemap_present: bool, url_count: int = 0) -> FactorVerdict:
    """Вердикт по XML sitemap: наличие."""
    if not sitemap_present:
        return FactorVerdict(
            factor="sitemap",
            verdict="warn",
            detail="XML sitemap не найден — краулерам сложнее обнаружить все страницы.",
            data={"present": False, "url_count": 0},
        )
    return FactorVerdict(
        factor="sitemap",
        verdict="pass",
        detail=f"XML sitemap найден ({url_count} URL).",
        data={"present": True, "url_count": url_count},
    )


def http_status_verdict(statuses: list[int]) -> FactorVerdict:
    """Вердикт по HTTP-кодам обойдённых страниц."""
    if not statuses:
        return FactorVerdict(
            factor="http_status",
            verdict="fail",
            detail="Ни одна страница не отдала HTTP-ответ — сайт недоступен.",
            data={"counts": {}},
        )
    server_err = [s for s in statuses if s >= 500]
    client_err = [s for s in statuses if 400 <= s < 500]
    counts = {"total": len(statuses), "4xx": len(client_err), "5xx": len(server_err)}
    if server_err:
        return FactorVerdict(
            factor="http_status",
            verdict="fail",
            detail=f"Обнаружены серверные ошибки 5xx на {len(server_err)} стр. — "
            "критично для индексации.",
            data={"counts": counts},
        )
    if client_err:
        return FactorVerdict(
            factor="http_status",
            verdict="warn",
            detail=f"Обнаружены клиентские ошибки 4xx на {len(client_err)} стр. "
            "(битые ссылки/удалённые страницы).",
            data={"counts": counts},
        )
    return FactorVerdict(
        factor="http_status",
        verdict="pass",
        detail=f"Все {len(statuses)} страниц отдали 2xx/3xx.",
        data={"counts": counts},
    )


def html_semantics_verdict(page_signals: list[dict[str, Any]]) -> FactorVerdict:
    """Вердикт по HTML-семантике: h1 и семантические теги на страницах."""
    if not page_signals:
        return FactorVerdict(
            factor="html_semantics",
            verdict="fail",
            detail="Нет страниц для анализа семантики.",
            data={},
        )
    with_h1 = sum(1 for s in page_signals if s.get("h1"))
    with_semantic = sum(1 for s in page_signals if s.get("semantic_tags"))
    total = len(page_signals)
    data = {"pages": total, "with_h1": with_h1, "with_semantic_tags": with_semantic}
    if with_h1 == 0:
        return FactorVerdict(
            factor="html_semantics",
            verdict="fail",
            detail="Ни на одной странице не найден <h1> — структура заголовков отсутствует.",
            data=data,
        )
    if with_h1 < total or with_semantic < total:
        return FactorVerdict(
            factor="html_semantics",
            verdict="warn",
            detail=f"<h1> найден на {with_h1}/{total} стр.; семантические теги — "
            f"на {with_semantic}/{total}. Часть страниц без явной структуры.",
            data=data,
        )
    return FactorVerdict(
        factor="html_semantics",
        verdict="pass",
        detail=f"На всех {total} страницах есть <h1> и семантические HTML5-теги.",
        data=data,
    )


def json_ld_verdict(page_signals: list[dict[str, Any]]) -> FactorVerdict:
    """Вердикт по наличию JSON-LD разметки (типы) на страницах."""
    types_found: set[str] = set()
    pages_with_ld = 0
    for signal in page_signals:
        blocks = signal.get("json_ld_blocks") or []
        if blocks:
            pages_with_ld += 1
        for block in blocks:
            types_found.update(_json_ld_types(block))
    data = {"types_found": sorted(types_found), "pages_with_json_ld": pages_with_ld}
    if not types_found:
        return FactorVerdict(
            factor="json_ld",
            verdict="fail",
            detail="JSON-LD разметка (schema.org) не найдена — AI-системам сложнее "
            "понять сущности сайта.",
            data=data,
        )
    return FactorVerdict(
        factor="json_ld",
        verdict="pass",
        detail=f"Найдена JSON-LD разметка типов: {', '.join(sorted(types_found))}.",
        data=data,
    )


def faq_verdict(page_signals: list[dict[str, Any]]) -> FactorVerdict:
    """Вердикт по наличию FAQ / answer-first блоков."""
    pages_with_faq = sum(1 for s in page_signals if s.get("faq_detected"))
    data = {"pages_with_faq": pages_with_faq, "pages": len(page_signals)}
    if pages_with_faq == 0:
        return FactorVerdict(
            factor="faq",
            verdict="warn",
            detail="FAQ / answer-first блоки не обнаружены — они повышают шанс "
            "цитирования в AI-ответах.",
            data=data,
        )
    return FactorVerdict(
        factor="faq",
        verdict="pass",
        detail=f"FAQ / answer-first блоки найдены на {pages_with_faq} стр.",
        data=data,
    )


def _json_ld_types(block: str) -> list[str]:
    """Извлечь значения @type из одного JSON-LD блока (best-effort; битый → пусто)."""
    try:
        parsed = json.loads(block)
    except (json.JSONDecodeError, TypeError):
        return []
    return _collect_types(parsed)


def _collect_types(node: Any) -> list[str]:
    """Рекурсивно собрать @type из JSON-LD (объекты, списки, @graph)."""
    types: list[str] = []
    if isinstance(node, dict):
        raw = node.get("@type")
        if isinstance(raw, str):
            types.append(raw)
        elif isinstance(raw, list):
            types.extend(t for t in raw if isinstance(t, str))
        for value in node.values():
            types.extend(_collect_types(value))
    elif isinstance(node, list):
        for item in node:
            types.extend(_collect_types(item))
    return types


def discover_links(html: str, base_url: str) -> list[str]:
    """Собрать внутренние ссылки (same-origin) со страницы для обхода."""
    from urllib.parse import urlparse

    soup = BeautifulSoup(html or "", "lxml")
    base_host = urlparse(base_url).netloc
    links: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not isinstance(href, str) or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href).split("#", 1)[0]
        if urlparse(absolute).netloc == base_host and absolute not in seen:
            seen.add(absolute)
            links.append(absolute)
    return links
