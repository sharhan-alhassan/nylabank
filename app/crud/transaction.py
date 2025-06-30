# app/crud/transaction.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.crud.base_crud import BaseCRUD

class CRUDTransaction(BaseCRUD[Transaction, TransactionCreate, TransactionUpdate]):
    async def get_by_reference_number(self, db: AsyncSession, *, reference_number: str) -> Optional[Transaction]:
        query = select(Transaction).filter(Transaction.reference_number == reference_number)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_account_id(self, db: AsyncSession, *, account_id: str) -> list[Transaction]:
        query = select(Transaction).filter(
            (Transaction.from_account_id == account_id) | (Transaction.to_account_id == account_id)
        )
        result = await db.execute(query)
        return result.scalars().all()

transaction_crud = CRUDTransaction(Transaction)