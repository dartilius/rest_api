# RMC Site API / API сайта RMC

NestJS API для сайта читает опубликованные данные, которыми управляют Django
и 1С. Он **не изменяет** исходные Django-таблицы и не выполняет их миграции.

The NestJS website API reads published data managed by Django and 1C. It
**never writes** Django source tables or runs Django migrations.

## Quick start / Быстрый старт

| What / Что | URL |
| --- | --- |
| Swagger UI | `http://localhost:3001/site-api/docs` |
| OpenAPI JSON | `http://localhost:3001/site-api/docs-json` |
| API base URL / Базовый URL | `http://localhost:3001/site-api/v1` |
| Health check / Проверка работоспособности | `http://localhost:3001/healthz` |

For local k3d, use `http://localhost:8080/site-api/v1` as the API base URL.
Для локального k3d используйте базовый URL `http://localhost:8080/site-api/v1`.

```powershell
Copy-Item .env.example .env
npm ci
npm run start:dev
```

Nest must use the read-only `nest_source_reader` PostgreSQL role, never Django
credentials. Nest должен использовать read-only роль `nest_source_reader`, а
не учётные данные Django.

## API conventions / Правила API

- JSON uses `camelCase`; UUID and prices are strings. Например: `"1250.00"`.
- Catalogue returns only `for_web=true` and `is_active=true` records.
- Lists use `limit` and `offset`.
- In `GET /nomenclatures`, arrays can be repeated or comma-separated:
  `brandIds=id1&brandIds=id2` or `brandIds=id1,id2`. POST bodies use JSON arrays.
- Errors always have this shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed."
  }
}
```

## Public catalogue / Публичный каталог

All catalogue endpoints are public / Все ручки каталога публичны.

### Brands / Бренды

```powershell
$base = 'http://localhost:8080/site-api/v1'
Invoke-RestMethod "$base/brands?search=demo&limit=20&offset=0"
Invoke-RestMethod "$base/brands/demo-brand"
```

`GET /brands/{identifier}` accepts UUID, slug, or 1C code. It returns
`404 BRAND_NOT_FOUND` when the brand is absent, deleted, or has no public
nomenclatures. UUID, slug или код 1С принимаются как `identifier`.

```json
{
  "data": [{
    "id": "00000000-0000-4000-8000-000000000010",
    "name": "Demo Brand",
    "slug": "demo-brand",
    "logoUrl": "https://media.example.local/local-media/brands/demo.png",
    "minPrice": "1250.00"
  }],
  "pagination": { "total": 1, "limit": 20, "offset": 0 }
}
```

### Nomenclatures / Номенклатуры

```powershell
Invoke-RestMethod "$base/nomenclatures?citySlug=krasnoyarsk&contentTypes=audio,video&priceFrom=1000.00&priceTo=5000.00&ordering=-pricePerMonth"
Invoke-RestMethod "$base/nomenclatures/demo-brand-krasnoyarsk"
```

`GET /nomenclatures/{identifier}` accepts UUID, 1C code, or legacy catalogue
slug. Its detail response also contains `fullAddress`, `description`, working
hours, `possibility`, and interior images.

### Filter options / Фасеты фильтра

`POST /nomenclatures/filter-options` returns valid contextual filter choices
and counts. Не передавайте `ordering`, `limit` и `offset` в body.

```powershell
$filters = @{
  citySlug = 'krasnoyarsk'
  brandIds = @('00000000-0000-4000-8000-000000000010')
  contentTypes = @('audio', 'video')
  priceFrom = '1000.00'
  priceTo = '5000.00'
  hasFacade = $true
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "$base/nomenclatures/filter-options" `
  -ContentType 'application/json' -Body $filters
```

The response has `brands`, `typesOfPlace`, `cities`, `contentTypes`,
`versions`, `timezones`, `statuses`, `hasFacade`, and `price`. Each facet
excludes its own selected filter, so a chosen brand does not hide alternatives.

### Map / Карта

`POST /nomenclatures/map` accepts the same JSON filters and returns all
matching map points without pagination.

```powershell
Invoke-RestMethod -Method Post -Uri "$base/nomenclatures/map" `
  -ContentType 'application/json' -Body '{"citySlug":"krasnoyarsk","hasFacade":true}'
```

`coordinates`, `brand`, `facade`, and `perDay` can be `null` when the source
record has insufficient data.

## Authentication / Авторизация

Django is the only token issuer. Nest does not log users in, refresh, or sign
tokens. Токены выдаёт только Django.

1. Obtain an access token from Django: `POST /auth/jwt/create/`.
2. Send it to Nest exactly as `Authorization: access_token <token>`.

```powershell
$login = Invoke-RestMethod -Method Post -Uri 'http://localhost:8080/auth/jwt/create/' `
  -ContentType 'application/json' `
  -Body '{"email":"user@example.test","password":"password"}'

Invoke-RestMethod "$base/auth/me" `
  -Headers @{ Authorization = "access_token $($login.access)" }
```

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "role": "ordinary",
  "tokenVersion": "rs256"
}
```

Without a valid token, `GET /auth/me` returns `401 UNAUTHORIZED`.

## Filtering reference / Справочник фильтров

| Field | Meaning / Значение |
| --- | --- |
| `search` | 1C code, RASB id, full-text search, or name prefix / код 1С, RASB id, полнотекстовый поиск или префикс названия |
| `status` | `0`, `1`, `2`; `null` — without status; `3` — do not filter / `null` — без статуса; `3` — не фильтровать |
| `contentTypes` | `audio`, `video`, `audio_video`, `audio_video_image`, `video_image`, `audio_image` |
| `priceFrom`, `priceTo` | Non-negative decimal strings; lower bound cannot exceed upper / неотрицательные decimal-строки, нижняя граница не выше верхней |
| `hasFacade` | `true` only with exterior image; `false` only without / только с фасадом или только без него |
| `ordering` | `default`, `name`, `pricePerMonth`, `version`, `timezone`, `brandName`, `legalEntityName`, `typeOfPlace`, `created`; `-` means descending / минус для убывания |

## Production boundary / Граница production

1. Configure `.env` from `.env.example` with `nest_source_reader`; run
   `npm run schema:verify` before enabling a database-backed feature.
2. Grant Nest only MinIO `s3:GetObject` permissions.
3. Keep Django's RSA private key only in Django/Celery secrets; Nest receives
   only `JWT_PUBLIC_KEY_PATH`.
4. Keep `JWT_ISSUER=rmc-django` and `JWT_AUDIENCE=rmc-site-api` identical in
   Django and Nest.

```powershell
npm run typecheck
npm test
npm run build
```
