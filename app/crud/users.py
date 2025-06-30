from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base_crud import BaseCRUD


class CRUDUser(BaseCRUD[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        query = select(User).filter(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        # Convert Address Pydantic object to dict if it exists
        address_dict = None
        if obj_in.address:
            address_dict = obj_in.address.model_dump()

        # Convert timezone-aware datetime to timezone-naive if it exists
        date_of_birth = None
        if obj_in.date_of_birth:
            # Remove timezone info to make it timezone-naive
            date_of_birth = obj_in.date_of_birth.replace(tzinfo=None)

        db_obj = User(
            email=obj_in.email,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            phone_number=obj_in.phone_number,
            date_of_birth=date_of_birth,  # Use timezone-naive datetime
            address=address_dict,  # Use the dictionary instead of Pydantic object
            hashed_password=get_password_hash(obj_in.password),
            is_active=True,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
    ) -> Optional[User]:
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user_crud = CRUDUser(User)
