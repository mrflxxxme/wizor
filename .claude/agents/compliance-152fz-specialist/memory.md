# compliance-152fz-specialist — memory

## Namespace
`memory/compliance-152fz-specialist.md`

## MUST-persist
- DPA-шаблон: текущая версия + история (founder-подписанные)
- Compliance-вердикты по провайдерам и типам данных (с датой)
- РКН-статус: уведомление подано/принято, дата, номер
- Перечень ПД-рисков в системе + вердикт по каждой точке
- Accepted-risk: founder-подписанные исключения (с датой истечения)

## MUST-NOT persist
- Реальные ПДн клиентов; секреты; полные юр-документы (только ссылки)

## Retrieval queries
- «Compliance-вердикт для [провайдер]»
- «Текущая версия DPA-шаблона»
- «РКН-статус»

## Write triggers
После каждого вердикта; после изменения DPA; после РКН-уведомления. `memory-curator` пишет.

## Pruning
Вердикты и accepted-risk — не удалять (аудиторский след); помечать expired/superseded.
