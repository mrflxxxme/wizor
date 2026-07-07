#!/usr/bin/env bash
# WIZOR SessionStart hook — founder-armed template (ADR-0020 executable layer).
# FOUNDER ACTION чтобы применить: `cp .claude/autonomy/session-start.hook.sh .claude/hooks/session-start.sh`
#   (+ применить settings.recommended.json, которая на него ссылается). Claude НЕ self-install'ит
#   авто-исполняемые хуки — это founder-owned переключатель.
# Что делает: авто-грузит контекст в КАЖДОЙ сессии (startup/resume/clear/compact), включая
# Agent-tool и headless `claude -p`. stdout попадает в контекст модели — держим компактно
# (charter §первое действие). Свежая/доп-сессия ориентируется без founder'а.
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
P="$ROOT/.planning"

echo "=== WIZOR · авто-контекст сессии (charter §первое действие) ==="
echo "Read-first (не грузи превентивно; остальное — JIT по MEMORY-INDEX.md):"
echo "  1. .planning/_meta/BUILD-CHARTER.md   (charter — целиком 1x/сессия)"
echo "  2. .planning/STATUS.md + .planning/HANDOFF.md   (где мы)"
echo "  3. .claude/agents/<role>/            (если ты профильный агент)"
echo "  4. .planning/roadmap/PNN-*.md        (активная фаза)"
echo "  5. .planning/contracts/<ctx>/        (затронутые контракты)"

if [ -f "$P/STATUS.md" ]; then
  echo ""
  echo "--- STATUS (rolling) ---"
  grep -E '^\*\*(Обновлено|Стадия)' "$P/STATUS.md" 2>/dev/null | sed 's/^/  /' || true
fi

if [ -f "$P/HANDOFF.md" ]; then
  echo ""
  echo "--- HANDOFF · следующее действие ---"
  awk '/^## (Следующее|Next|Состояние)/{f=1} f&&/^## /&&!/^## (Следующее|Next|Состояние)/&&NR>3{exit} f' "$P/HANDOFF.md" \
    2>/dev/null | head -8 | sed 's/^/  /' || true
fi

echo ""
echo "=== Автономия (ADR-0021): /autonomy:run · :discuss · :ack · :heal ==="
echo "=== 9-шаговый цикл (charter §4): Scope→Plan→Domain→Implement→Review→Verify→Audit→Memory→PR ==="
echo "=== Человек — ТОЛЬКО на гейте фазы (founder_signature, ADR-0017). Внутри фазы агенты автономны. ==="
exit 0
