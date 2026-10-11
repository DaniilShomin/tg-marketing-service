# Экспорт персональных данных

## Эндпоинт

`GET /auth/me/personal-data/export/` или
`POST /auth/me/personal-data/export/` скачивает JSON-файл с персональными
данными текущего авторизованного пользователя.

Параметры пользователя в URL или теле запроса не принимаются. Сервер всегда
определяет субъекта по аутентифицированной сессии. Ответ нельзя кэшировать.

## Ответ

- `Content-Type: application/json; charset=utf-8`
- `Content-Disposition: attachment; filename="personal-data-<id>-<date>.json"`
- `Cache-Control: no-store`

Корневая схема формата `1.0`:

```json
{
  "format_version": "1.0",
  "exported_at": "2026-09-29T12:00:00+00:00",
  "subject_id": 42,
  "personal_data": {
    "profile": {},
    "owned_groups": [],
    "channel_moderator_assignments": [],
    "ai_insights": [],
    "partner_profile": {}
  },
  "processing_information": {
    "processing_confirmed": true,
    "purposes": [],
    "legal_basis": [],
    "retention_terms": [],
    "personal_data_fields": {}
  }
}
```

`partner_profile` присутствует только при наличии партнёрского профиля.
Денежное поле `balance` передаётся строкой, чтобы не терять точность. Даты
передаются в ISO 8601, отсутствующие даты — как `null`. Порядок элементов в
массивах стабилен по внутреннему `id`.

Экспорт содержит только группы, назначения модератором и AI-инсайты текущего
пользователя. Профили авторов каналов и записи других модераторов в файл не
включаются. Каждый успешный экспорт фиксируется в журнале запросов субъектов.
