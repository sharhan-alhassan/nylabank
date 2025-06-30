from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate
from app.crud.base_crud import BaseCRUD

class CRUDAccount(BaseCRUD[Account, AccountCreate, AccountUpdate]):
    async def get_by_account_number(self, db: AsyncSession, *, account_number: str) -> Optional[Account]:
        query = select(Account).filter(Account.account_number == account_number)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> list[Account]:
        query = select(Account).filter(Account.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all()

account_crud = CRUDAccount(Account) 