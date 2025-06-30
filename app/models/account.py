from sqlalchemy import String, Enum, Numeric, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..db.base_class import Base, UUIDMixin
from typing import TYPE_CHECKING
import enum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction
else:
    User = "User"
    Transaction = "Transaction"


class AccountType(enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"


class AccountStatus(enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Account(Base, UUIDMixin):
    __tablename__ = "accounts"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    account_number: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)

    balance: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2), default=0.00, nullable=False
    )
    currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False
    )

    overdraft_limit: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2), default=0.00, nullable=False
    )
    interest_rate: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True
    )  # For savings accounts

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    from_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.from_account_id",
        back_populates="from_account",
    )
    to_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.to_account_id",
        back_populates="to_account",
    )
