"""Celery-задача ``run_probe_batch`` — оркестрация probe-мониторинга (P5, AC-1/AC-6).

Поток: загрузить активный набор промптов сайта (tenant-scoped) → для каждой модели ×
промпта × прогона (N≥5) вызвать доменный ``ProbeRunner.run_prompt`` → сохранить сырые
``probe_runs`` → агрегировать (``metrics.engine``) → сохранить ``visibility_metrics``.

Fault-isolation (AC-1/AC-6): сбой отдельного прогона НЕ роняет батч — упавший прогон
сохраняется с ``error`` и исключается из успешных при агрегации. Модель, у которой ПРОВАЛены
все прогоны, логируется как ``provider_failed`` (не ``batch_failed``) — остальные модели
обрабатываются успешно. ``ProbeRunner`` импортируется лениво (собирается параллельно
crawler-probe-specialist'ом); в unit-тестах :func:`_load_runner` монкипатчится.

Момент времени (``run_at`` упавших прогонов, ``calculated_at`` агрегата) — на границе
задачи; чистый движок метрик часов не читает (детерминизм).
"""

from __future__ import annotations

import asyncio
import datetime
import importlib
import uuid
from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from urllib.parse import urlparse

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.db.session import get_sessionmaker
from wizor.iam.models import Site
from wizor.llm_router.uncertainty import MIN_RUNS
from wizor.metrics.engine import aggregate_visibility
from wizor.metrics.repository import save_visibility_metrics
from wizor.probe.repository import load_active_prompt_set, save_probe_runs
from wizor.probe.schemas import (
    FOREIGN_MODELS,
    RU_MODELS,
    Egress,
    ModelId,
    ProbeRun,
)
from wizor.worker.celery_app import celery_app

logger = structlog.get_logger(__name__)

# 4 probe-модели MVP; порядок детерминирован (RU-ноды, затем иностранные через прокси).
PROBE_MODELS: tuple[ModelId, ...] = RU_MODELS + FOREIGN_MODELS
# N≥5 прогонов на промпт×модель (FR-2.3, §6.7) — база для честного CI.
RUNS_PER_PROMPT = MIN_RUNS


@runtime_checkable
class _ProbeRunnerSeam(Protocol):
    """Ожидаемый шов доменного probe-раннера (structural typing; строится параллельно).

    ``run_prompt`` выполняет N≥5 прогонов промпта на модели: сам крутит N-цикл, выбирает
    гео-ноду (dual-geo, §6.4), ротацию прокси, вызывает модель, парсит (``mentioned``/``cited``)
    и ловит per-run сбои → error-runs. Раннер владеет geo/egress/N-циклом/парсингом; задача
    оркеструет промпт×модель и персистит.
    """

    async def run_prompt(
        self,
        *,
        prompt_id: str,
        prompt: str,
        model: ModelId,
        n_runs: int,
        brand_terms: Sequence[str],
    ) -> list[ProbeRun]:
        """Выполнить N≥5 probe-прогонов промпта на модели (dual-geo + парсинг внутри).

        ``brand_terms`` — per-site бренд/домен-термы для эвристики mention/citation (пер-сайт,
        НЕ глобальный env → multi-tenant-safe). Без них ``detect_mention_citation`` вернёт
        ``(False, False)`` и все метрики выродятся к базовому уровню — шов ОБЯЗАН их нести.
        """
        ...  # pragma: no cover — Protocol-заглушка


def _egress_for(model: ModelId) -> Egress:
    """Ожидаемый гео-класс исходящего для модели (§6.4: иностранная → только 'foreign')."""
    return "foreign" if model in FOREIGN_MODELS else "ru"


def _site_brand_terms(url: str) -> list[str]:
    """Стартовые бренд/домен-термы из URL сайта (ЧИСТО, без сети): метка домена + полный хост.

    ``https://www.example.com/x`` → ``["example", "example.com"]``: метка регистрируемого
    домена (бренд-терм → mention) + полный хост без ``www``/порта/userinfo (домен-терм с точкой
    → citation). Эвристика без public-suffix-list: метка = предпоследний лейбл хоста. Пустой или
    непарсибельный хост → ``[]``.

    # deferred: rich entity brand-terms (продукты, алиасы из crawler entity-extraction) → P6.
    """
    netloc = urlparse(url).netloc
    host = netloc.rsplit("@", 1)[-1].rsplit(":", 1)[0].strip().lower()
    host = host.removeprefix("www.")
    if not host:
        return []
    labels = [label for label in host.split(".") if label]
    terms: list[str] = []
    if len(labels) >= 2:  # «домен.tld»: бренд-метка = предпоследний лейбл
        terms.append(labels[-2])
    elif labels:
        terms.append(labels[0])
    if host not in terms:
        terms.append(host)  # полный хост — домен-терм (содержит '.', → citation)
    return terms


def _load_runner() -> _ProbeRunnerSeam:
    """Лениво подтянуть доменный :class:`ProbeRunner` (собирается параллельно).

    Динамический импорт (не статический), чтобы задача не ломалась на импорте, пока доменный
    модуль ещё не готов. Точка для monkeypatch в unit-тестах. Модуль/класс отсутствует или не
    реализует шов → явная ошибка (без раннера probe невозможен — не тихий провал).
    """
    module = importlib.import_module("wizor.probe.runner")
    runner_cls = getattr(module, "ProbeRunner", None)
    if runner_cls is None:
        msg = "wizor.probe.runner.ProbeRunner недоступен (probe-раннер собирается параллельно)"
        raise RuntimeError(msg)
    instance = runner_cls()
    if not isinstance(instance, _ProbeRunnerSeam):
        msg = "ProbeRunner не реализует ожидаемый шов run_prompt(...)"
        raise TypeError(msg)
    return instance


async def collect_probe_runs(
    runner: _ProbeRunnerSeam,
    prompts: Sequence[str],
    *,
    brand_terms: Sequence[str],
    now: datetime.datetime,
) -> tuple[list[ProbeRun], list[ModelId]]:
    """Прогнать модели × промпты × N прогонов с fault-isolation (AC-1/AC-6). ЧИСТО от БД.

    Возвращает ``(runs, failed_models)``. Сбой одного прогона → синтетический ``ProbeRun`` с
    ``error`` (батч не падает); модель со 100% провалом попадает в ``failed_models``. Ключ
    промпта — индекс в наборе (стабилен между прогонами одной версии). ``brand_terms`` —
    per-site термы mention/citation — прокидываются в КАЖДЫЙ ``run_prompt`` (без них метрики
    инертны).
    """
    all_runs: list[ProbeRun] = []
    failed_models: list[ModelId] = []
    for model in PROBE_MODELS:
        model_runs: list[ProbeRun] = []
        any_success = False
        for idx, prompt_text in enumerate(prompts):
            prompt_id = str(idx)
            try:
                prompt_runs = list(
                    await runner.run_prompt(
                        prompt_id=prompt_id,
                        prompt=prompt_text,
                        model=model,
                        n_runs=RUNS_PER_PROMPT,
                        brand_terms=brand_terms,
                    )
                )
            except Exception as exc:  # wholesale-сбой раннера → синтетические error-runs (AC-6)
                prompt_runs = [
                    ProbeRun(
                        prompt_id=prompt_id,
                        model=model,
                        run_index=i,
                        raw_response="",
                        mentioned=False,
                        cited=False,
                        egress=_egress_for(model),
                        run_at=now,
                        error=str(exc),
                    )
                    for i in range(RUNS_PER_PROMPT)
                ]
            if any(r.error is None for r in prompt_runs):
                any_success = True
            model_runs.extend(prompt_runs)
        if model_runs and not any_success:
            failed_models.append(model)
        all_runs.extend(model_runs)
    return all_runs, failed_models


async def _load_site_url(
    session: AsyncSession, *, tenant_id: uuid.UUID, site_id: uuid.UUID
) -> str | None:
    """URL сайта строго в рамках тенанта (§6.8; mirror crawler ``_load_site_url``). Нет → None."""
    stmt = select(Site.url).where(Site.id == site_id, Site.tenant_id == tenant_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def _run(tenant_id: uuid.UUID, site_id: uuid.UUID) -> dict[str, object]:
    """Асинхронное тело задачи: набор промптов → прогоны → persist → агрегат → persist."""
    now = datetime.datetime.now(tz=datetime.UTC)
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        prompt_set = await load_active_prompt_set(session, tenant_id=tenant_id, site_id=site_id)
        site_url = await _load_site_url(session, tenant_id=tenant_id, site_id=site_id)
    if prompt_set is None:
        logger.warning("probe.no_prompt_set", tenant_id=str(tenant_id), site_id=str(site_id))
        return {"status": "no_prompt_set", "site_id": str(site_id)}

    # Per-site бренд/домен-термы (multi-tenant-safe: из URL сайта, НЕ глобальный env). Богатые
    # термы (продукты/алиасы из entity-extraction) — # deferred: rich entity brand-terms → P6.
    if site_url:
        brand_terms = _site_brand_terms(site_url)
    else:
        logger.warning("probe.no_site_url", tenant_id=str(tenant_id), site_id=str(site_id))
        brand_terms = []

    runner = _load_runner()
    runs, failed_models = await collect_probe_runs(
        runner, prompt_set.prompts, brand_terms=brand_terms, now=now
    )

    for model in failed_models:
        # AC-6: провал одного провайдера — provider_failed, а НЕ batch_failed.
        logger.warning(
            "provider_failed",
            model=model,
            tenant_id=str(tenant_id),
            site_id=str(site_id),
            prompt_set_version=prompt_set.version,
        )

    _aggregates, metrics = aggregate_visibility(runs, prompt_set_version=prompt_set.version)

    async with sessionmaker() as session:
        await save_probe_runs(session, tenant_id=tenant_id, site_id=site_id, runs=runs)
        await save_visibility_metrics(
            session, tenant_id=tenant_id, site_id=site_id, metrics=metrics, calculated_at=now
        )
        await session.commit()

    logger.info(
        "probe.batch.completed",
        tenant_id=str(tenant_id),
        site_id=str(site_id),
        runs=len(runs),
        models=len(PROBE_MODELS),
        failed_models=len(failed_models),
        prompts=len(prompt_set.prompts),
        visibility_score=metrics.visibility_score,
        n=metrics.n,
        prompt_set_version=prompt_set.version,
    )
    return {
        "status": "completed",
        "site_id": str(site_id),
        "runs": len(runs),
        "failed_models": [str(model) for model in failed_models],
        "visibility_score": metrics.visibility_score,
        "prompt_set_version": prompt_set.version,
    }


@celery_app.task(name="wizor.run_probe_batch")  # type: ignore[untyped-decorator]  # Celery decorator не типизирован
def run_probe_batch(site_id: str, tenant_id: str) -> dict[str, object]:
    """Enqueue-точка: probe-батч сайта ``site_id`` тенанта ``tenant_id`` (read-only, dual-geo).

    Аргументы — строки (JSON-сериализация брокера); парсятся в UUID. Синхронная Celery-обёртка
    гоняет async-тело в собственном loop (``asyncio.run``).
    """
    return asyncio.run(_run(uuid.UUID(tenant_id), uuid.UUID(site_id)))
