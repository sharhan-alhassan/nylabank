from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from app.schemas.base import BaseSchema
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from app.models.transaction import TransactionType, TransactionStatus


class TransactionBase(BaseSchema):
    transaction_type: TransactionType
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field(..., description="Transaction currency")
    description: Optional[str] = Field(None, description="Transaction description")
    reference_number: str = Field(..., description="Unique reference number")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    balance_after: Optional[Decimal] = Field(None, description="Balance after transaction")
    transaction_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional transaction metadata")
    processed_at: Optional[datetime] = Field(None, description="When transaction was processed")


class TransactionCreate(TransactionBase):
    from_account_id: Optional[UUID] = Field(None, description="Source account ID")
    to_account_id: Optional[UUID] = Field(None, description="Destination account ID")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v
    
    @validator('reference_number')
    def validate_reference_number(cls, v):
        if len(v) < 6:
            raise ValueError('Reference number must be at least 6 characters long')
        return v.upper()


class TransactionUpdate(BaseSchema):
    transaction_type: Optional[TransactionType] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    status: Optional[TransactionStatus] = None
    balance_after: Optional[Decimal] = None
    transaction_metadata: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None
    from_account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None


class TransactionInDBBase(TransactionBase):
    id: UUID
    from_account_id: Optional[UUID]
    to_account_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class Transaction(TransactionInDBBase):
    pass


class TransactionInDB(TransactionInDBBase):
    pass


# Specific transaction types
class DepositRequest(BaseSchema):
    account_id: UUID = Field(..., description="Account to deposit into")
    amount: Decimal = Field(..., description="Amount to deposit")
    description: Optional[str] = Field(None, description="Deposit description")


class WithdrawRequest(BaseSchema):
    account_id: UUID = Field(..., description="Account to withdraw from")
    amount: Decimal = Field(..., description="Amount to withdraw")
    description: Optional[str] = Field(None, description="Withdrawal description")


class TransferRequest(BaseSchema):
    from_account_id: UUID = Field(..., description="Source account ID")
    to_account_id: UUID = Field(..., description="Destination account ID")
    amount: Decimal = Field(..., description="Amount to transfer")
    description: Optional[str] = Field(None, description="Transfer description")


class TransactionList(BaseSchema):
    total_count: int
    page: int
    per_page: int
    total_pages: int
    data: List[Transaction]


class TransactionCreateResponse(BaseSchema):
    detail: str
    transaction: Transaction


class TransactionReverseRequest(BaseSchema):
    reason: str = Field(..., description="Reason for reversing the transaction")


class TransactionReverseResponse(BaseSchema):
    detail: str
    original_transaction: Transaction
    reversal_transaction: Transaction


class TransactionFilter(BaseSchema):
    account_id: Optional[UUID] = None
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    limit: Optional[int] = Field(10, ge=1, le=100)
    skip: Optional[int] = Field(0, ge=0) 