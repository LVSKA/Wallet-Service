import asyncio

import pytest
from httpx import AsyncClient

from app.models.wallet import Wallet

pytestmark = pytest.mark.asyncio


async def test_concurrent_deposits_do_not_lose_updates(
    client: AsyncClient, existing_wallet: Wallet
) -> None:
    """
    20 параллельных депозитов по 10 на один и тот же кошелёк.

    Тесты используют in-memory SQLite (единственное соединение через
    StaticPool), поэтому запросы физически сериализуются самим драйвером,
    а не блокировкой строки, которую даёт `FOR UPDATE` на Postgres.
    Проверка защищает от логических ошибок сервисного слоя (например,
    чтения и записи баланса вне одной транзакции); настоящую блокировку
    строки на конкурентных транзакциях подтверждает работа с реальным
    Postgres в docker-compose.
    """
    deposits_count = 20
    amount = 10

    async def deposit() -> None:
        response = await client.post(
            f"/api/v1/wallets/{existing_wallet.id}/operation",
            json={"operation_type": "DEPOSIT", "amount": amount},
        )
        assert response.status_code == 200

    await asyncio.gather(*(deposit() for _ in range(deposits_count)))

    response = await client.get(f"/api/v1/wallets/{existing_wallet.id}")
    expected_balance = existing_wallet.balance + deposits_count * amount
    assert response.json()["balance"] == expected_balance


async def test_concurrent_withdraw_never_goes_negative(
    client: AsyncClient, existing_wallet: Wallet
) -> None:
    """
    existing_wallet стартует с балансом 1000. Запускаем 20 параллельных
    списаний по 100 (итого 2000, вдвое больше баланса) — ровно половина
    должна пройти успешно, остальные — получить 400, баланс не должен
    уйти в минус.
    """
    withdraw_count = 20
    amount = 100

    async def withdraw() -> int:
        response = await client.post(
            f"/api/v1/wallets/{existing_wallet.id}/operation",
            json={"operation_type": "WITHDRAW", "amount": amount},
        )
        return response.status_code

    results = await asyncio.gather(*(withdraw() for _ in range(withdraw_count)))

    successful = results.count(200)
    failed = results.count(400)

    assert successful == 10
    assert failed == 10

    response = await client.get(f"/api/v1/wallets/{existing_wallet.id}")
    assert response.json()["balance"] == 0
