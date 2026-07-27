# Wallet Service

REST API для операций с кошельками пользователей на FastAPI + PostgreSQL.

## Запуск

```bash
docker compose up --build
```

Поднимутся три сервиса: `db` (Postgres), `migrate` (разово прогоняет
alembic-миграции) и `api` (само приложение на `http://localhost:8000/docs`).

## Эндпоинты

- `POST /api/v1/wallets` — создать кошелёк (баланс 0).
- `GET /api/v1/wallets/{wallet_id}` — получить баланс.
- `POST /api/v1/wallets/{wallet_id}/operation` — изменить баланс:

```json
{
  "operation_type": "DEPOSIT",
  "amount": 1000
}
```

`operation_type` — `DEPOSIT` или `WITHDRAW`, `amount` — целое положительное
число. При недостатке средств на `WITHDRAW` возвращается `400`, при
отсутствии кошелька — `404`.

## Конкурентность

Операция изменения баланса выполняется в одной транзакции с
`SELECT ... FOR UPDATE` по строке кошелька: конкурентные запросы к одному
и тому же кошельку блокируются на уровне БД и применяются последовательно,
поэтому параллельные депозиты/списания не теряют друг друга и баланс не
уходит в отрицательные значения.

## Тесты

```bash
docker compose run --rm api pytest -v
```

Тесты гоняются на том же Postgres, что поднимает docker-compose (отдельный engine с NullPool, изоляция между тестами — через truncate/rollback), включают отдельные проверки на конкурентные запросы к одному кошельку.

## Миграции

Миграции лежат в `migrations/versions`. Применяются автоматически сервисом
`migrate` при `docker compose up`. Чтобы сгенерировать новую после правки
моделей:

```bash
docker compose run --rm api alembic revision --autogenerate -m "message"
```
