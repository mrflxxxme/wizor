# `evidence/` — коммит-привязанные evidence-артефакты (ADR-0021 D3)

Усиливает live-gold (ADR-0018) до неподделываемого на мёрже. Local-only гейты (funded live-gold crawl/probe, Docker-интеграция, адверсариальный аудит), которые GitHub CI прогнать не может, пишут сюда доказательство прогона.

## Протокол

1. Гейт-скрипт/роль пишет `evidence/<gate>.json` по [`../.claude/autonomy/evidence-schema.json`](../.claude/autonomy/evidence-schema.json), с `head_sha` = точный коммит прогона и `verdict` = `PASS`/`FAIL`.
2. Фаза заявляет требуемые гейты в `evidence/manifest.json`:
   ```json
   { "phase": "P2", "required_gates": ["live_golden_crawl", "adversarial_audit"] }
   ```
3. CI-job `evidence.yml` гоняет `verify_evidence.py`: каждый заявленный гейт существует, **свежий** (`head_sha` == PR head), `PASS`. Иначе мёрж заблокирован.

**Свежесть — зубы:** коммит после генерации evidence → tip ушёл → evidence протух → CI красный → пере-прогнать против финального коммита. Агент не может смёржить зелёное, заявив непрогнанный против смёрженного кода гейт.

## Гейты WIZOR

| gate id | что | когда |
|---|---|---|
| `live_golden_crawl` | живой crawl golden-набора (read-only) | P2, P6, P8 |
| `live_golden_probe` | живой dual-geo probe (N≥5+CI, ноль РФ-IP) | P5, P6 |
| `docker_integration` | integration против реальных PG/Redis/Keycloak | infra-фазы |
| `adversarial_audit` | 3/5-линзовый пост-аудит + 10 инвариантов §6 | все фазы (риск-тир) |

Артефакты `evidence/*.json` — рантайм-вывод гейтов, коммитятся на ветке фазы (не руками). Без `manifest.json` job `evidence` проходит тривиально (фазы без local-only гейтов не затронуты).
