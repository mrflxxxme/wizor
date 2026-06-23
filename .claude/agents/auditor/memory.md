# auditor — memory

**namespace:** `agent-memory:auditor`
**owned files:** `_session-context/AUDIT-YYYY-MM-DD-<phase>/` (до архивации)

## MUST-persist
- Паттерны invariant-нарушений по типу и фазе
- История BLOCKED-вердиктов (причина + фаза)
- Accepted-risk решения (founder-подписанные deferred-to-AC)

## MUST-NOT
- Secrets, PII, даже найденные (только pointer file:line)
- Полный код диффа
- Компромиссные вердикты ("почти PASS") — строго PASS/PASS-WITH-FIXES/BLOCKED

## Retrieval queries
- `tag:invariant-violation inv:<N>` — нарушения конкретного инварианта §6
- `tag:blocked-reason phase:<PNN>` — причины BLOCKED по фазам
- `tag:accepted-risk` — founder-signed deferred findings

## Pruning
AUDIT-файлы → архив после merge (memory-curator). Accepted-risk — держи постоянно (не удалять без новой founder-подписи).
