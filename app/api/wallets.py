import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.wallet import OperationRequest, WalletResponse
from app.services import wallet_service
from app.services.exceptions import InsufficientFundsError, WalletNotFoundError

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(session: AsyncSession = Depends(get_session)) -> WalletResponse:
    wallet = await wallet_service.create_wallet(session)
    return WalletResponse.model_validate(wallet)


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> WalletResponse:
    try:
        wallet = await wallet_service.get_balance(session, wallet_id)
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Кошелёк не найден"
        ) from exc
    return WalletResponse.model_validate(wallet)


@router.post("/{wallet_id}/operation", response_model=WalletResponse)
async def perform_operation(
    wallet_id: uuid.UUID,
    payload: OperationRequest,
    session: AsyncSession = Depends(get_session),
) -> WalletResponse:
    try:
        wallet = await wallet_service.apply_operation(
            session, wallet_id, payload.operation_type, payload.amount
        )
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Кошелёк не найден"
        ) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return WalletResponse.model_validate(wallet)
