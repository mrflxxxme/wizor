# plan-quality checklist (planner)

Запускать перед финализацией PLAN.md.

- [ ] Каждая задача имеет уникальный `id`
- [ ] Каждая задача имеет явный `role` (backend-implementer / frontend-implementer / specialist)
- [ ] Каждая задача имеет `tier` и `model` (Sonnet/Opus/Haiku)
- [ ] Каждая задача имеет ≥1 измеримый AC
- [ ] Каждая задача имеет `contracts_touched` (список bounded-context'ов)
- [ ] `depends_on` заполнен корректно (нет циклических зависимостей)
- [ ] Specialist задачи идут ДО implementer задач (если фаза domain-специфична)
- [ ] Scope не противоречит ни одному из 10 инвариантов charter §6
- [ ] Нет задач, которые нарушают read-only-границу Tier 0/Manual (инвариант §6.1)
- [ ] PLAN.md содержит HEAD-SUMMARY (≤500 токенов) в начале
