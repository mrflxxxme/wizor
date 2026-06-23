<!-- HEAD-SUMMARY (≤500т): Реестр TBD-токенов, необходимых перед переходом в production. Охватывает: Yandex Cloud аккаунт, ЮKassa мерчант, Keycloak realm, LLM provider API-ключи (GigaChat/YandexGPT/OpenAI/Perplexity), резидентные прокси, РФ юрлицо, бренд/домен, РКН-уведомление, GitHub org, PostHog. Обновляется при заполнении токенов. -->

# PLACEHOLDERS — реестр TBD-токенов для production

> Обновляется при заполнении. Токен считается заполненным, когда в колонке `Status` стоит `done` и есть ссылка на Vault/Lockbox или ADR. Никогда не записывать реальные значения в этот файл — только ссылки.

## Инфраструктура и аккаунты

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `YANDEX_CLOUD_ORG_ID` | Yandex Cloud organization ID (основной аккаунт для РФ-хостинга, 152-ФЗ) | TODO | — |
| `YANDEX_CLOUD_FOLDER_ID` | Folder ID для prod-окружения | TODO | — |
| `YANDEX_CLOUD_SERVICE_ACCOUNT_KEY` | JSON-ключ сервисного аккаунта (CI/CD, Terraform) | TODO | Yandex Lockbox |
| `YANDEX_LOCKBOX_SECRET_ID` | ID Lockbox-хранилища секретов prod | TODO | — |
| `HETZNER_PROJECT_ID` | Hetzner Cloud project (зарубежные probe-ноды) | TODO | — |
| `SELECTEL_PROJECT_ID` | Selectel project (резервный зарубежный probe) | TODO | — |
| `GITHUB_ORG` | GitHub organization name (или GitLab group для РФ CI) | TODO | — |
| `DOCKER_REGISTRY_URL` | Yandex Container Registry URL для prod-образов | TODO | — |

## Биллинг

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `YUKASSA_SHOP_ID` | ЮKassa merchant shop ID (приём оплат, физ + юр лица, СБП) | TODO | Yandex Lockbox |
| `YUKASSA_SECRET_KEY` | ЮKassa secret key для API | TODO | Yandex Lockbox |
| `STRIPE_PUBLISHABLE_KEY` | Stripe (экспорт, фаза B) | TODO | Yandex Lockbox |
| `STRIPE_SECRET_KEY` | Stripe secret (экспорт, фаза B) | TODO | Yandex Lockbox |

## Auth

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `KEYCLOAK_REALM_NAME` | Имя realm для WIZOR prod (Keycloak self-hosted) | TODO | — |
| `KEYCLOAK_CLIENT_ID` | OIDC client ID (backend + frontend) | TODO | Yandex Lockbox |
| `KEYCLOAK_CLIENT_SECRET` | OIDC client secret | TODO | Yandex Lockbox |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin credentials | TODO | Yandex Lockbox |

## LLM Provider API-ключи

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `GIGACHAT_API_KEY` | GigaChat API (Сбер) — RU-default для генерации контента и probe | TODO | Yandex Lockbox |
| `GIGACHAT_SCOPE` | GigaChat scope (GIGACHAT_API / GIGACHAT_API_CORP) | TODO | — |
| `YANDEX_GPT_API_KEY` | YandexGPT + Yandex Foundation Models (probe Алиса/Нейро + embeddings) | TODO | Yandex Lockbox |
| `YANDEX_GPT_FOLDER_ID` | Folder ID для YandexGPT API-запросов | TODO | — |
| `OPENAI_API_KEY` | OpenAI (ChatGPT probe + fallback; только через зарубежные ноды) | TODO | Yandex Lockbox |
| `PERPLEXITY_API_KEY` | Perplexity API (probe; только через зарубежные ноды) | TODO | Yandex Lockbox |
| `ANTHROPIC_API_KEY` | Anthropic Claude (A.4+, opt-in для не-чувствительных задач) | TODO | Yandex Lockbox |

## Crawler / Прокси

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `SMARTPROXY_USERNAME` | Smartproxy — резидентные прокси (ChatGPT/Perplexity probe без РФ-IP) | TODO | Yandex Lockbox |
| `SMARTPROXY_PASSWORD` | Smartproxy password | TODO | Yandex Lockbox |
| `BRIGHTDATA_API_KEY` | Bright Data — резервный провайдер резидентных прокси | TODO | Yandex Lockbox |

## Юридическое / Compliance

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `RU_LEGAL_ENTITY_INN` | ИНН российского юр. лица (обязательно для ЮKassa, B2B-договоров, 152-ФЗ) | TODO | — |
| `RU_LEGAL_ENTITY_NAME` | Полное наименование юр. лица (ООО / ИП) | TODO | — |
| `RKN_NOTIFICATION_NUMBER` | Номер уведомления Роскомнадзора об операторе ПД (NFR-1, 152-ФЗ) | TODO | — |
| `DPA_TEMPLATE_VERSION` | Версия DPA-соглашения, принятая compliance-specialist | TODO | `decisions/ADR-NNNN` |

## Бренд / Домен

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `BRAND_DOMAIN_RU` | Основной домен сайта (напр. wizor.ru) — регистрация + DNS | TODO | — |
| `BRAND_DOMAIN_COM` | Международный домен (фаза B/C) | TODO | — |
| `BRAND_NAME` | Юридически защищённое торговое наименование (товарный знак РФ) | TODO | — |

## Аналитика / Нотификации

| Токен | Назначение | Статус | Значение / Ссылка |
|---|---|---|---|
| `POSTHOG_API_KEY` | PostHog self-hosted API key (North Star, воронка, NFR-7) | TODO | Yandex Lockbox |
| `POSTHOG_HOST` | URL self-hosted PostHog инстанса | TODO | — |
| `SENTRY_DSN` | Sentry DSN для error tracking (backend + frontend) | TODO | Yandex Lockbox |
| `TELEGRAM_BOT_TOKEN` | Telegram bot для алертов деградации (FR-5.4) | TODO | Yandex Lockbox |
| `MAILGUN_API_KEY` | Mailgun / Unisender — email-нотификации (FR-5.4, P9) | TODO | Yandex Lockbox |

## Как работать с этим реестром

1. При заполнении токена: обновить `Status` → `done`, добавить ссылку на Lockbox-путь или ADR.
2. **Никогда** не записывать реальные значения в этот файл — только ссылки на Vault / Lockbox.
3. Перед каждой tier-4 фазой: проверить, что все токены фазы заполнены (`security-auditor` / `compliance-152fz-specialist`).
4. Незаполненные токены = блокер деплоя в prod (часть Definition of Done tier 3+).
