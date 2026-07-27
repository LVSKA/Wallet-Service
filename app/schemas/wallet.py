import enum
import uuid

from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: int = Field(gt=0, description="Сумма операции, целое число больше нуля")


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    balance: int
