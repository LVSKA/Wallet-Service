import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.schemas.wallet import OperationType
from app.services.exceptions import InsufficientFundsError, WalletNotFoundError


async def get_balance(session: AsyncSession, wallet_id: uuid.UUID) -> Wallet:
    wallet = await session.get(Wallet, wallet_id)
    if wallet is None:
        raise WalletNotFoundError(str(wallet_id))
    return wallet


async def apply_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType | str,
    amount: Decimal | int,
) -> Wallet:
    stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
    result = await session.execute(stmt)
    wallet = result.scalar_one_or_none()

    if wallet is None:
        raise WalletNotFoundError(str(wallet_id))

    # Сравнение через str(), чтобы корректно обрабатывать и Enum, и обычную строку
    is_deposit = str(operation_type).upper() == "DEPOSIT" or operation_type == OperationType.DEPOSIT

    if is_deposit:
        wallet.balance += amount
    else:
        if wallet.balance < amount:
            raise InsufficientFundsError(
                f"Недостаточно средств на кошельке {wallet_id}"
            )
        wallet.balance -= amount

    await session.commit()
    return wallet


async def create_wallet(session: AsyncSession) -> Wallet:
    wallet = Wallet(balance=0)
    session.add(wallet)
    await session.commit()
    return wallet