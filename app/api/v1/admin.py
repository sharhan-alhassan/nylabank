from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
from app.crud.users import user_crud
from app.crud.accounts import account_crud
from app.crud.transaction import transaction_crud
from app.db.session import get_async_session
from app.schemas.user import UserList
from app.schemas.account import AccountList
from app.schemas.transaction import TransactionList, TransactionType, TransactionStatus
from app.core.deps import get_current_admin
from app.models.user import UserRole, User
from app.models.account import AccountStatus, AccountType
from app.models.transaction import TransactionType, TransactionStatus
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import traceback


class AdminRouter:
    def __init__(self):
        self.router = APIRouter()
        self.prefix = "/admin"
        self.tags = ["admin"]
        self.singular = "admin"
        self.plural = "admins"

        self.router.add_api_route(
            "/users",
            self.list_all_users,
            methods=["GET"],
            response_model=UserList,
            summary="List all users (Admin only)",
        )

        self.router.add_api_route(
            "/accounts",
            self.list_all_accounts,
            methods=["GET"],
            response_model=AccountList,
            summary="List all accounts (Admin only)",
        )

        self.router.add_api_route(
            "/transactions",
            self.list_all_transactions,
            methods=["GET"],
            response_model=TransactionList,
            summary="List all transactions (Admin only)",
        )

        self.router.add_api_route(
            "/accounts/{account_id}/freeze",
            self.freeze_account,
            methods=["POST"],
            summary="Freeze account (Admin only)",
        )

        self.router.add_api_route(
            "/reports/daily-summary",
            self.daily_summary,
            methods=["GET"],
            summary="Get daily summary report (Admin only)",
        )

    async def list_all_users(
        self,
        page: int = 1,
        per_page: int = 10,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_admin),
    ) -> Any:
        """List all users (Admin only) with pagination"""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 50:
                per_page = 10

            skip = (page - 1) * per_page

            # Build filters
            filters = {}
            if role:
                filters["role"] = role
            if is_active is not None:
                filters["is_active"] = is_active

            # Get users with filters
            users = await user_crud.filter(
                db, filters=filters, limit=per_page, skip=skip, order_by=["-created_at"]
            )

            # Calculate pagination info
            total_count = users["total_count"]
            total_pages = (total_count + per_page - 1) // per_page

            return {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "data": users["data"],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving users: {str(e)}",
            )

    async def list_all_accounts(
        self,
        page: int = 1,
        per_page: int = 10,
        status: Optional[AccountStatus] = None,
        account_type: Optional[AccountType] = None,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_admin),
    ) -> Any:
        """List all accounts (Admin only) with pagination"""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 50:
                per_page = 10

            skip = (page - 1) * per_page

            # Build filters
            filters = {}
            if status:
                filters["status"] = status
            if account_type:
                filters["account_type"] = account_type

            # Get accounts with filters
            accounts = await account_crud.filter(
                db, filters=filters, limit=per_page, skip=skip, order_by=["-created_at"]
            )

            # Calculate pagination info
            total_count = accounts["total_count"]
            total_pages = (total_count + per_page - 1) // per_page

            return {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "data": accounts["data"],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving accounts: {str(e)}",
            )

    async def list_all_transactions(
        self,
        page: int = 1,
        per_page: int = 10,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_admin),
    ) -> Any:
        """List all transactions (Admin only) with pagination"""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 50:
                per_page = 10

            skip = (page - 1) * per_page

            # Build filters
            filters = {}
            if transaction_type:
                filters["transaction_type"] = transaction_type
            if status:
                filters["status"] = status
            if start_date:
                filters["created_at__gte"] = start_date
            if end_date:
                filters["created_at__lte"] = end_date

            # Get transactions with filters
            transactions = await transaction_crud.filter(
                db, filters=filters, limit=per_page, skip=skip, order_by=["-created_at"]
            )

            # Calculate pagination info
            total_count = transactions["total_count"]
            total_pages = (total_count + per_page - 1) // per_page

            return {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "data": transactions["data"],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving transactions: {str(e)}",
            )

    async def freeze_account(
        self,
        account_id: UUID,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_admin),
    ) -> Any:
        """Freeze account (Admin only)"""
        try:
            # Get the account
            account = await account_crud.get_or_404(db, account_id)

            # Check if account is already frozen
            if account.status == AccountStatus.FROZEN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account is already frozen",
                )

            # Freeze the account
            frozen_account = await account_crud.update(
                db, db_obj=account, obj_in={"status": AccountStatus.FROZEN}
            )

            return {
                "detail": f"Account {frozen_account.account_number} frozen successfully",
                "account_id": frozen_account.id,
                "status": frozen_account.status,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error freezing account: {str(e)}",
            )

    async def daily_summary(
        self,
        date: Optional[str] = None,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_admin),
    ) -> Any:
        """Get daily summary report (Admin only)"""
        try:
            # Use provided date or today
            if date:
                try:
                    report_date = datetime.strptime(date, "%Y-%m-%d").date()
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid date format. Use YYYY-MM-DD",
                    )
            else:
                report_date = datetime.now().date()

            # Calculate date range for the day
            start_datetime = datetime.combine(report_date, datetime.min.time())
            end_datetime = datetime.combine(report_date, datetime.max.time())

            # Get daily statistics
            # Total users
            total_users = await user_crud.count(db)
            new_users_today = await user_crud.count(
                db,
                filters={
                    "created_at__gte": start_datetime,
                    "created_at__lte": end_datetime,
                },
            )

            # Total accounts
            total_accounts = await account_crud.count(db)
            active_accounts = await account_crud.count(
                db, filters={"status": AccountStatus.ACTIVE}
            )

            # Total transactions
            total_transactions = await transaction_crud.count(db)

            # Transactions today
            today_transactions = await transaction_crud.count(
                db,
                filters={
                    "created_at__gte": start_datetime,
                    "created_at__lte": end_datetime,
                },
            )

            # Calculate total transaction volume today
            from app.models.transaction import Transaction
            from sqlalchemy import func

            # This is a simplified calculation - you might want to use proper aggregation
            total_volume_today = Decimal("0.00")  # Placeholder

            # Get transaction types breakdown
            deposit_count = await transaction_crud.count(
                db,
                filters={
                    "transaction_type": TransactionType.DEPOSIT,
                    "created_at__gte": start_datetime,
                    "created_at__lte": end_datetime,
                },
            )

            withdrawal_count = await transaction_crud.count(
                db,
                filters={
                    "transaction_type": TransactionType.WITHDRAWAL,
                    "created_at__gte": start_datetime,
                    "created_at__lte": end_datetime,
                },
            )

            transfer_count = await transaction_crud.count(
                db,
                filters={
                    "transaction_type": TransactionType.TRANSFER,
                    "created_at__gte": start_datetime,
                    "created_at__lte": end_datetime,
                },
            )

            return {
                "date": report_date.isoformat(),
                "summary": {
                    "users": {"total": total_users, "new_today": new_users_today},
                    "accounts": {"total": total_accounts, "active": active_accounts},
                    "transactions": {
                        "total": total_transactions,
                        "today": today_transactions,
                        "volume_today": total_volume_today,
                    },
                    "transaction_types": {
                        "deposits": deposit_count,
                        "withdrawals": withdrawal_count,
                        "transfers": transfer_count,
                    },
                },
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating daily summary: {str(e)}",
            )


admin_router = AdminRouter()
