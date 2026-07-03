# RUN-QUEUE — autonomous runner interrupt queue

> Append-only лог interrupt-событий runner'а (ADR-0021 D8): ack-needed / escalation / revert / stuck / complete. Pending-записи ждут founder'а; резолвь через `/autonomy:ack <ID> <verdict>`. Пишется `scripts/autonomy/run_queue.py` — руками не редактируй.

<!-- Записи ниже добавляет run_queue.py. Пусто = ничего не ждёт founder'а. -->
