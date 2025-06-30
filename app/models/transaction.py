from sqlalchemy import DateTime, String, Boolean, Enum, JSON, Numeric, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..db.base_class import Base, UUIDMixin
from typing import TYPE_CHECKING
from datetime import datetime
import enum

if TYPE_CHECKING:
    from app.models.account import Account
else:
    Account = "Account"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    FEE = "fee"


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class Transaction(Base, UUIDMixin):
    __tablename__ = "transactions"

    from_account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), nullable=True, index=True
    )
    to_account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), nullable=True, index=True
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    reference_number: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )

    balance_after: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )
    transaction_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    processed_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    # Relationships
    from_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[from_account_id], back_populates="from_transactions"
    )
    to_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[to_account_id], back_populates="to_transactions"
    )
