import uuid

import pytest
from httpx import AsyncClient

from app.models.wallet import Wallet

pytestmark = pytest.mark.asyncio


async def test_create_wallet(client: AsyncClient) -> None:
    response = await client.post("/api/v1/wallets")

    assert response.status_code == 201
    body = response.json()
    assert body["balance"] == 0
    uuid.UUID(body["id"])  # не падает, значит валидный uuid


async def test_get_balance(client: AsyncClient, existing_wallet: Wallet) -> None:
    response = await client.get(f"/api/v1/wallets/{existing_wallet.id}")

    assert response.status_code == 200
    assert response.json()["balance"] == 1000


async def test_get_balance_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/wallets/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_deposit_increases_balance(client: AsyncClient, existing_wallet: Wallet) -> None:
    response = await client.post(
        f"/api/v1/wallets/{existing_wallet.id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 500},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == 1500


async def test_withdraw_decreases_balance(client: AsyncClient, existing_wallet: Wallet) -> None:
    response = await client.post(
        f"/api/v1/wallets/{existing_wallet.id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 300},
    )

    assert response.status_code == 200
    assert response.json()["balance"] == 700


async def test_withdraw_insufficient_funds(client: AsyncClient, existing_wallet: Wallet) -> None:
    response = await client.post(
        f"/api/v1/wallets/{existing_wallet.id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 999999},
    )

    assert response.status_code == 400


async def test_operation_wallet_not_found(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/wallets/{uuid.uuid4()}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100},
    )

    assert response.status_code == 404


async def test_operation_rejects_negative_amount(
    client: AsyncClient, existing_wallet: Wallet
) -> None:
    response = await client.post(
        f"/api/v1/wallets/{existing_wallet.id}/operation",
        json={"operation_type": "DEPOSIT", "amount": -10},
    )

    assert response.status_code == 422


async def test_operation_rejects_invalid_type(
    client: AsyncClient, existing_wallet: Wallet
) -> None:
    response = await client.post(
        f"/api/v1/wallets/{existing_wallet.id}/operation",
        json={"operation_type": "TRANSFER", "amount": 10},
    )

    assert response.status_code == 422
