from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.otp import Otp
from app.schemas.otp import OtpCreate, OtpUpdate
from app.crud.base_crud import BaseCRUD


class CRUDOtp(BaseCRUD[Otp, OtpCreate, OtpUpdate]):
    async def get_otp_by_email(self, db: AsyncSession, *, email: str) -> Optional[Otp]:
        query = select(Otp).filter(Otp.email == email)
        result = await db.execute(query)
        return result.scalars().first()


otp_crud = CRUDOtp(Otp)
