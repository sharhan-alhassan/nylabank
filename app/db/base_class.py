from sqlalchemy import MetaData
from typing import Any
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, Integer, DateTime, func, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.config import settings

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata_obj = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    __abstract__ = True  # This ensures the base class doesn't create its own table
    metadata = metadata_obj


# # Mixin for Integer primary key
# class IntegerIDMixin:
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     created_at = Column(
#         DateTime(timezone=True), server_default=func.now(), nullable=False
#     )
#     updated_at = Column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         onupdate=func.now(),
#         nullable=False,
#     )


# # Mixin for UUID primary key
# class UUIDMixin:
#     id = Column(
#         UUID(as_uuid=True),
#         primary_key=True,
#         default=lambda: (uuid.uuid4()),
#         index=True,
#     )
#     created_at = Column(
#         DateTime(timezone=True), server_default=func.now(), nullable=False
#     )
#     updated_at = Column(
#         DateTime(timezone=True),
#         server_default=func.now(),
#         onupdate=func.now(),
#         nullable=False,
#     )


# Mixin for Integer primary key
class IntegerIDMixin:
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# Mixin for UUID primary key
class UUIDMixin:
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid4(),
        index=True,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

# created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
# updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    