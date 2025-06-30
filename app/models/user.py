from sqlalchemy import DateTime, String, Boolean, Enum, JSON, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..db.base_class import Base, UUIDMixin
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import enum
import json

if TYPE_CHECKING:
    from app.models.account import Account
else:
    Account = "Account"

class UserRole(enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class User(Base, UUIDMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=False, index=True)
    date_of_birth: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="user", cascade="all, delete-orphan")
