"""Pydantic v2 DTO-шов контекста crawler (P2).

Единственная граница типов между crawler-модулем (домен) и persistence-слоем
(Celery/БД). crawler возвращает `CrawlResult`; backend маппит его в строку
`crawl_results`. Менять форму — согласованно с обоими слоями (charter §7 контракт).
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Verdict = Literal["pass", "warn", "fail", "deferred"]
"""Вердикт аудит-фактора. `deferred` — фактор не проверен (нет ключа/адаптера), не «fail»."""


class FactorVerdict(BaseModel):
    """Вердикт по одному аудит-фактору (AC-2)."""

    factor: str
    """Идентификатор фактора: robots_txt|sitemap|http_status|html_semantics|
    json_ld|faq|cwv|indexability."""
    verdict: Verdict
    detail: str
    """Человекочитаемое пояснение (RU) — почему pass/warn/fail/deferred."""
    data: dict[str, Any] = Field(default_factory=dict)
    """Факт-специфичная нагрузка (напр. список найденных JSON-LD типов)."""


class PageAudit(BaseModel):
    """Результат аудита одной страницы."""

    url: str
    http_status: int
    content_hash: str
    """sha256 нормализованного отрендеренного HTML — основа P8 re-crawl delta."""
    rendered_via_js: bool
    """True, если JS-рендер (Playwright) изменил контент относительно сырого HTML (SPA, AC-3)."""
    signals: dict[str, Any] = Field(default_factory=dict)
    """Извлечённые структурные сигналы: h1–h3, семантические теги, JSON-LD блоки, FAQ-блоки."""


class SchemaValidation(BaseModel):
    """Результат валидации JSON-LD разметки (FR-1.2, AC-4)."""

    schema_valid: bool
    types_found: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    """Причины невалидности (AC-4: пользователь видит причину)."""


class CrawlResult(BaseModel):
    """Полный структурированный результат краула сайта — потребляется P3 (Score)."""

    site_url: str
    crawled_at: datetime
    pages: list[PageAudit] = Field(default_factory=list)
    audit_summary: list[FactorVerdict] = Field(default_factory=list)
    schema_validation: SchemaValidation
    read_only_confirmed: bool
    """True = guard подтвердил ноль не-GET запросов к внешним доменам (AC-7, §6.1)."""
    error: str | None = None
    """Установлено, если краул провалился целиком (сайт недоступен и т.п.)."""
