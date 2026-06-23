---
id: ADR-0016
title: llms-txt-not-citation-weighted
status: accepted
date: 2026-06-23
supersedes: []
---
<!-- HEAD-SUMMARY (≤500т): llms.txt не входит в citation-вес и AI-Readiness Score; позиционируется как agent-infra Integration layer, не citation-драйвер; honest-uncertainty: Visibility-% только как диапазон+доверие при N≥5+CI. -->

## Context

llms.txt был анонсирован как стандарт для LLM-индексации. Маркетинговое давление — включить его в Score и позиционировать как citation-левер. Рыночная верификация (июнь 2026, PRD §7.1): AI-поисковые краулеры практически не читают llms.txt (408 обращений из 500M визитов AI-ботов); Google его не поддерживает; удаление llms.txt-переменной из citation-моделей улучшало их точность. Риск «llms.txt-theater» (PRD §14): продукт обещает то, чего нет → утрата доверия при верификации.

Параллельная проблема: LLM-Visibility метрики недетерминированы. Без доверительного интервала «Visibility +30%» — маркетинговая ложь, проверяемая при re-crawl.

## Decision

**llms.txt не весит в citation-компоненте AI-Readiness Score** (стоячий инвариант №5 Charter §6). В продукте llms.txt **генерируется** (дёшево, future-proof для агентов/IDE/MCP), переносится в **Integration layer** (PRD §7.3), но позиционируется только как agent-infra артефакт. Citation-левер — schema.org JSON-LD + FAQ/answer-first блоки (доказано: +44% цитирований).

**Honest-uncertainty doctrine** (PRD §3, p.2): все Visibility-прогнозы показываются только как диапазон + уровень доверия при N≥5 прогонах + CI. Никаких гарантированных «Visibility X%» в UI/marketing. «Реальное» улучшение = выход за полосу шума. Предиктивная site-specific модель — roadmap-айтем после накопления Auto-track данных, не MVP-обещание.

Проверяется как стоячие инварианты №2, №5, №7 в каждом аудите.

## Consequences

- Readiness Score отражает реальные citation-факторы; не замусоривается «theater»-метриками.
- Клиент видит честный прогноз; верификация при re-crawl подтверждает, а не опровергает обещания.
- WIZOR строит доверие через доказательность, а не маркетинговый шум.
- llms.txt по-прежнему генерируется и отдаётся клиенту — future-proof, не игнорируется.
- Компромисс: конкуренты могут позиционировать llms.txt как «фичу» — WIZOR берёт верхнюю позицию «честного экспертного инструмента».
- N≥5 probe + CI = операционный overhead, но это цена честной метрики.

## Alternatives considered

| Альтернатива | Pro | Contra | Почему отклонили |
|---|---|---|---|
| llms.txt в Score с высоким весом | Маркетинговая простота | Метрика лжёт; верификация провалится; репутационный ущерб | Нарушает honest-uncertainty doctrine |
| Не генерировать llms.txt вообще | Нет theater | Теряем future-proof для agent/MCP-сценариев | Генерация дёшева; агент-инфра ценна в фазе C |
| Показывать Visibility-% без CI | Простой UI | Обещания, которые не верифицируются → churn | Нарушает два стоячих инварианта |

## Links

- Charter: `BUILD-CHARTER.md §6 (инварианты 2,5,7)`
- PRD: `PRD.md §7.1, §7.3, §9.2 (FR-1.3, FR-2.3, FR-3.5), §14 (риск llms.txt-theater), §3 (p.2 honest-uncertainty)`
- Related ADRs: ADR-0005 (post-audit invariants), ADR-0012 (three-track)
