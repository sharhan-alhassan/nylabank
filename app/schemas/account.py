from typing import Optional, List
from pydantic import BaseModel, Field, validator
from app.schemas.base import BaseSchema
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from app.models.account import AccountType, AccountStatus


class AccountBase(BaseSchema):
    account_type: AccountType
    balance: Decimal = Field(..., description="Account balance")
    currency: str = Field(default="USD", description="Account currency")
    status: AccountStatus = Field(default=AccountStatus.ACTIVE)
    overdraft_limit: Decimal = Field(default=0.00, description="Overdraft limit")
    interest_rate: Optional[Decimal] = Field(None, description="Interest rate for savings accounts (as decimal, e.g., 0.05 for 5%)")
    
    @validator('interest_rate')
    def validate_interest_rate(cls, v):
        if v is not None:
            # Convert percentage to decimal if it's a whole number > 1
            if v > 1:
                v = v / 100
            # Ensure it fits within the database constraint (precision=5, scale=4)
            if v >= 10:  # Max value for precision=5, scale=4 is 9.9999
                raise ValueError('Interest rate must be less than 1000%')
        return v


class AccountCreate(AccountBase):
    user_id: UUID = Field(..., description="User ID who owns this account")

class AccountUpdate(BaseSchema):
    account_number: Optional[str] = None
    account_type: Optional[AccountType] = None
    balance: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[AccountStatus] = None
    overdraft_limit: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = Field(None, description="Interest rate for savings accounts (as decimal, e.g., 0.05 for 5%)")
    
    @validator('interest_rate')
    def validate_interest_rate(cls, v):
        if v is not None:
            # Convert percentage to decimal if it's a whole number > 1
            if v > 1:
                v = v / 100
            # Ensure it fits within the database constraint (precision=5, scale=4)
            if v >= 10:  # Max value for precision=5, scale=4 is 9.9999
                raise ValueError('Interest rate must be less than 1000%')
        return v


class AccountInDBBase(AccountBase):
    id: UUID
    user_id: UUID
    account_number: str = Field(..., description="Unique account number")
    created_at: datetime
    updated_at: datetime


class Account(AccountInDBBase):
    pass


class AccountInDB(AccountInDBBase):
    pass


class AccountBalance(BaseSchema):
    account_id: UUID
    account_number: str
    balance: Decimal
    currency: str
    last_updated: datetime


class AccountStatement(BaseSchema):
    account_id: UUID
    account_number: str
    start_date: date
    end_date: date
    opening_balance: Decimal
    closing_balance: Decimal
    transactions: List[dict]  # Will be populated with transaction details


class AccountList(BaseSchema):
    total_count: int
    page: int
    per_page: int
    total_pages: int
    data: List[Account]


class AccountCreateResponse(BaseSchema):
    detail: str
    account: Account


class AccountUpdateResponse(BaseSchema):
    detail: str
    account: Account
    
class AccountCloseResponse(BaseSchema):
    detail: str
    account_id: UUID 
    