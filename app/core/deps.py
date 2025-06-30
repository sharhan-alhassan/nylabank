from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.crud.users import user_crud
from app.db.session import get_async_session
from app.models.user import User, UserRole
from datetime import datetime
from app.schemas.tokens import TokenPayloadSchema

oauth2_scheme = OAuth2PasswordBearer(
    # The endpoing that returns the access_token, usually the /token or /login endpoints
    tokenUrl=f"{settings.API_V1_STR}/users/login",
    scheme_name="JWT",
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayloadSchema(**payload)

        # If no user found
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token is expired
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exception

    user = await user_crud.get(db, id=token_data.sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden: You are not an admin")
    return current_user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=400, detail="Inactive user: Your account is not active"
        )
    return current_user
