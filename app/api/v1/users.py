from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app.core.security import create_access_token
from app.crud.users import user_crud
from app.crud.otps import otp_crud
from app.db.session import get_async_session
from app.schemas.user import (
    User,
    UserCreate,
    GenericDetailResponse,
    LoginResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    # UserAccountDeletedResponse,
)
from app.schemas.otp import OtpCreate, OtpConfirm
from fastapi.security import OAuth2PasswordRequestForm
from app.core.deps import get_current_user
from app.config import settings
from app.utility import (
    generate_otp_code,
    send_email_verification_code,
    send_password_reset_email,
    send_welcome_email,
)
from datetime import datetime, timedelta
from app.utilities.logger import logger


class UserRouter:
    def __init__(self):
        self.router = APIRouter()
        self.prefix = "/users"
        self.tags = ["users"]
        self.singular = "user"
        self.plural = "users"

        self.router.add_api_route(
            "/register",
            self.register,
            methods=["POST"],
            response_model=GenericDetailResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register new user",
        )

        self.router.add_api_route(
            "/login",
            self.login,
            methods=["POST"],
            summary="User login",
            status_code=status.HTTP_200_OK,
            response_model=LoginResponse,
            description="""
            
            """,
        )

        self.router.add_api_route(
            "/confirm-registration",
            self.confirm_registration,
            methods=["POST"],
            response_model=GenericDetailResponse,
            summary="User confirm registration with an OTP",
        )

        self.router.add_api_route(
            "/send-otp",
            self.send_otp,
            methods=["POST"],
            response_model=GenericDetailResponse,
            summary="User resend OTP to complete registration.",
        )

        self.router.add_api_route(
            "/me",
            self.get_me,
            methods=["GET"],
            response_model=User,
            summary="Get current user",
        )

        self.router.add_api_route(
            "/password-reset",
            self.request_password_reset,
            methods=["POST"],
            response_model=GenericDetailResponse,
            summary="Request password reset",
        )

        self.router.add_api_route(
            "/password-reset/confirm",
            self.confirm_password_reset,
            methods=["POST"],
            response_model=GenericDetailResponse,
            summary="Confirm password reset with OTP",
        )

    async def register(
        self, user_in: UserCreate, db: AsyncSession = Depends(get_async_session)
    ) -> Any:
        if user_in.password != user_in.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        user = await user_crud.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists! If this is your account, request an OTP to activate your account",
            )

        user = await user_crud.create(db, obj_in=user_in)
        otp_code = generate_otp_code()

        expiration_time = datetime.utcnow() + timedelta(minutes=settings.OTP_LIFESPAN)
        otp_data = OtpCreate(
            email=user_in.email,
            otp_code=otp_code,
            expires_on=expiration_time,
            is_expired=False,
        )

        await otp_crud.create(db, obj_in=otp_data)

        try:
            await send_email_verification_code(
                {
                    "verify_code": otp_code,
                    "email_to": user.email,
                    "name": user.first_name.title(),
                }
            )
            return {
                "detail": f"Registration successful for {user.email}. Check your email for OTP to activate your account."
            }
        except Exception as e:
            logger.error(f"Failed to send registration otp: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to send verification email"
            )

    async def login(
        self,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_session),
    ) -> Any:
        existing_user = await user_crud.get_by_email(db, email=form_data.username)
        if not existing_user:
            raise HTTPException(detail="User does not exists", status_code=400)
        user = await user_crud.authenticate(
            db,
            email=form_data.username.lower(),
            password=form_data.password,
        )
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="User not active. Please request an OTP and activate your account.",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(user.id, access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}

    async def confirm_registration(
        self, data: OtpConfirm, db: AsyncSession = Depends(get_async_session)
    ) -> Any:
        user = await user_crud.get_by_email(db, email=data.email)
        if not user:
            raise HTTPException(
                status_code=400, detail="User does not exist or wrong email"
            )

        otp = await otp_crud.get_by(db=db, filters={"email": data.email})

        if not otp:
            raise HTTPException(
                status_code=400, detail="OTP not found. Please request a new OTP."
            )

        if otp.is_expired or otp.expires_on < datetime.utcnow():
            await otp_crud.update(db=db, db_obj=otp, obj_in={"is_expired": True})
            raise HTTPException(
                status_code=400, detail="OTP has expired. Please request a new OTP."
            )

        if otp.otp_code != data.otp_code:
            raise HTTPException(status_code=400, detail="Incorrect OTP code.")

        await otp_crud.delete(db=db, id=otp.id)
        update_data = {"is_active": True}
        await user_crud.update(db=db, db_obj=user, obj_in=update_data)

        # Send welcome email
        try:
            await send_welcome_email(
                {
                    "email_to": user.email,
                    "first_name": user.first_name.title(),
                    "last_name": user.last_name.title(),
                    "email": user.email,
                    "account_type": user.role.value,
                    "join_date": user.created_at.strftime("%B %d, %Y"),
                    "dashboard_url": f"{settings.FRONTEND_URL}/dashboard",
                }
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")

        return {
            "detail": "Account successfully activated. Please proceed to login!",
        }

    async def send_otp(
        self,
        email: str,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_async_session),
    ) -> Any:
        user = await user_crud.get_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=400, detail="User does not exist. Please register first."
            )

        otp = await otp_crud.get_by(db=db, filters={"email": email})

        if otp:
            await otp_crud.delete(db=db, id=otp.id)

        otp_code = generate_otp_code()
        logger.info(f"OTP code ({otp_code}) generated for {email}")

        new_otp = OtpCreate(
            email=email,
            otp_code=otp_code,
            expires_on=datetime.utcnow() + timedelta(minutes=settings.OTP_LIFESPAN),
            is_expired=False,
        )

        await otp_crud.create(db=db, obj_in=new_otp)

        async def send_email_task(otp_code: str, email: str, name: str):
            try:
                await send_email_verification_code(
                    {
                        "verify_code": otp_code,
                        "email_to": email,
                        "name": name,
                    }
                )
                logger.info(f"OTP successfully sent to {email}")
            except Exception as e:
                logger.error(f"Email sending error: {str(e)}")

        background_tasks.add_task(
            send_email_task,
            otp_code=otp_code,
            email=email,
            name=user.first_name.title(),
        )

        return {
            "detail": "OTP sent. Check your email to activate your account.",
            "status": status.HTTP_200_OK,
        }

    async def get_me(
        self,
        current_user: User = Depends(get_current_user),
    ) -> Any:
        return current_user

    async def request_password_reset(
        self,
        data: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_async_session),
    ) -> Any:
        user = await user_crud.get_by_email(db, email=data.email)
        if not user:
            # Don't reveal if user exists or not for security
            return {"detail": "A password reset code has been sent to your email."}

        # Delete existing OTP for this email
        existing_otp = await otp_crud.get_by(db=db, filters={"email": data.email})
        if existing_otp:
            await otp_crud.delete(db=db, id=existing_otp.id)

        reset_code = generate_otp_code()
        logger.info(f"Password reset code ({reset_code}) generated for {data.email}")

        new_otp = OtpCreate(
            email=data.email,
            otp_code=reset_code,
            expires_on=datetime.utcnow()
            + timedelta(minutes=15),  # 15 minutes for password reset
            is_expired=False,
        )

        await otp_crud.create(db=db, obj_in=new_otp)

        async def send_reset_email_task(reset_code: str, email: str):
            try:
                await send_password_reset_email(
                    {"reset_code": reset_code, "email_to": email}
                )
                logger.info(f"Password reset email successfully sent to {email}")
            except Exception as e:
                logger.error(f"Password reset email sending error: {str(e)}")

        background_tasks.add_task(
            send_reset_email_task, reset_code=reset_code, email=data.email
        )

        return {"detail": "A password reset code has been sent to your email."}

    async def confirm_password_reset(
        self,
        data: PasswordResetConfirm,
        db: AsyncSession = Depends(get_async_session),
    ) -> Any:
        if data.new_password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        user = await user_crud.get_by_email(db, email=data.email)
        if not user:
            raise HTTPException(status_code=400, detail="User does not exist")

        otp = await otp_crud.get_by(db=db, filters={"email": data.email})
        if not otp:
            raise HTTPException(
                status_code=400,
                detail="Reset code not found. Please request a new one.",
            )

        if otp.is_expired or otp.expires_on < datetime.utcnow():
            await otp_crud.update(db=db, db_obj=otp, obj_in={"is_expired": True})
            raise HTTPException(
                status_code=400,
                detail="Reset code has expired. Please request a new one.",
            )

        if otp.otp_code != data.reset_code:
            raise HTTPException(status_code=400, detail="Incorrect reset code.")

        # Update password
        from app.core.security import get_password_hash

        hashed_password = get_password_hash(data.new_password)
        await user_crud.update(
            db=db, db_obj=user, obj_in={"hashed_password": hashed_password}
        )

        # Delete the OTP
        await otp_crud.delete(db=db, id=otp.id)

        return {
            "detail": "Password successfully reset. You can now login with your new password."
        }


user_router = UserRouter()
