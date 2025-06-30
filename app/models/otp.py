from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base, UUIDMixin

class Otp(Base, UUIDMixin):
    __tablename__ = "otps"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    otp_code: Mapped[str] = mapped_column(String, index=True)
    expires_on: Mapped[DateTime] = mapped_column(DateTime)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)