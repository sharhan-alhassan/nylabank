from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app.crud.accounts import account_crud
from app.db.session import get_async_session
from app.schemas.account import (
    Account,
    AccountCreate,
    AccountUpdate,
    AccountBalance,
    AccountStatement,
    AccountList,
    AccountCreateResponse,
    AccountUpdateResponse,
    AccountCloseResponse,
)
from app.core.deps import get_current_user
from app.models.user import UserRole, User
from app.models.account import AccountStatus
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import random
import string
from app.utilities import logger

def generate_account_number() -> str:
    """Generate a unique 12-digit account number"""
    # Generate 12 random digits
    digits = ''.join(random.choices(string.digits, k=12))
    return digits


class AccountRouter:
    def __init__(self):
        self.router = APIRouter()
        self.prefix = "/accounts"
        self.tags = ["accounts"]
        self.singular = "account"
        self.plural = "accounts"

        self.router.add_api_route(
            "/",
            self.list_accounts,
            methods=["GET"],
            response_model=AccountList,
            summary="List user's accounts",
        )

        self.router.add_api_route(
            "/",
            self.create_account,
            methods=["POST"],
            response_model=AccountCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create new account",
        )

        self.router.add_api_route(
            "/{account_id}",
            self.get_account,
            methods=["GET"],
            response_model=Account,
            summary="Get account details",
        )

        self.router.add_api_route(
            "/{account_id}",
            self.update_account,
            methods=["PUT"],
            response_model=AccountUpdateResponse,
            summary="Update account details",
        )

        self.router.add_api_route(
            "/{account_id}",
            self.delete_account,
            methods=["DELETE"],
            summary="Delete account (hard delete)",
        )

        self.router.add_api_route(
            "/{account_id}/close",
            self.close_account,
            methods=["POST"],
            response_model=AccountCloseResponse,
            summary="Close account (soft delete)",
        )
        
        self.router.add_api_route(
            "/{account_id}/balance",
            self.get_balance,
            methods=["GET"],
            response_model=AccountBalance,
            summary="Get current balance",
        )

        self.router.add_api_route(
            "/{account_id}/statement",
            self.get_statement,
            methods=["GET"],
            response_model=AccountStatement,
            summary="Get account statement",
        )

    async def list_accounts(
        self,
        page: int = 1,
        per_page: int = 10,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """List user's accounts with pagination"""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 50:
                per_page = 10
            
            skip = (page - 1) * per_page
            
            # For customers, only show their own accounts
            # For admins, show all accounts
            if current_user.role == UserRole.CUSTOMER:
                accounts = await account_crud.filter(
                    db,
                    filters={"user_id": current_user.id},
                    limit=per_page,
                    skip=skip
                )
            else:
                # Admin can see all accounts
                accounts = await account_crud.all(db, limit=per_page, skip=skip)

            # Calculate pagination info
            total_count = accounts["total_count"]
            total_pages = (total_count + per_page - 1) // per_page

            return {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "data": accounts["data"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving accounts: {str(e)}"
            )

    async def create_account(
        self,
        account_in: AccountCreate,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Create new account with auto-generated account number"""
        try:
            # Ensure user can only create accounts for themselves (unless admin)
            if current_user.role == UserRole.CUSTOMER and account_in.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create accounts for yourself"
                )

            # Generate unique account number
            max_attempts = 10
            for attempt in range(max_attempts):
                account_number = generate_account_number()
                
                # Check if account number already exists
                existing_account = await account_crud.get_by_account_number(db, account_number=account_number)
                if not existing_account:
                    break
                
                if attempt == max_attempts - 1:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to generate unique account number"
                    )

            # Create account data with generated account number
            account_data = account_in.model_dump()
            account_data["account_number"] = account_number

            # Create the account
            account = await account_crud.create(db, obj_in=account_data)

            return {
                "detail": f"Account {account.account_number} created successfully",
                "account": account
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating account: {str(e)}"
            )

    async def get_account(
        self,
        account_id: UUID,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Get account details"""
        try:
            account = await account_crud.get_or_404(db, account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            return account
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving account: {str(e)}"
            )

    async def update_account(
        self,
        account_id: UUID,
        account_in: AccountUpdate,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Update account details"""
        try:
            account = await account_crud.get_or_404(db, account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            # Update the account
            updated_account = await account_crud.update(db, db_obj=account, obj_in=account_in)

            return {
                "detail": f"Account {updated_account.account_number} updated successfully",
                "account": updated_account
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating account: {str(e)}"
            )

    async def delete_account(
        self,
        account_id: UUID,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Delete account (hard delete)"""
        try:
            account = await account_crud.get_or_404(db, account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            # Hard delete the account
            await account_crud.delete(db, id=account_id)

            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting account: {str(e)}"
            )

    async def close_account(
        self,
        account_id: UUID,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Close account (soft delete)"""
        try:
            account = await account_crud.get_or_404(db, account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            # Soft delete by setting status to CLOSED
            update_data = {"status": AccountStatus.CLOSED}
            closed_account = await account_crud.update(db, db_obj=account, obj_in=update_data)

            return {
                "detail": f"Account {closed_account.account_number} closed successfully",
                "account_id": closed_account.id
            }
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error closing account: {str(e)}"
            )

    async def get_balance(
        self,
        account_id: UUID,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Get current balance"""
        try:
            account = await account_crud.get_or_404(db, account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            return {
                "account_id": account.id,
                "account_number": account.account_number,
                "balance": account.balance,
                "currency": account.currency,
                "last_updated": account.updated_at
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving balance: {str(e)}"
            )

    async def get_statement(
        self,
        account_id: UUID,
        start_date: str,
        end_date: str,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Get account statement"""
        try:
            account = await account_crud.get_or_404(db, account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            # Parse dates
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )

            # Get transactions for the date range
            from app.crud.transaction import transaction_crud
            
            # Get all transactions for this account (both incoming and outgoing)
            incoming_transactions = await transaction_crud.filter(
                db,
                filters={"to_account_id": account_id},
                limit=100
            )
            
            outgoing_transactions = await transaction_crud.filter(
                db,
                filters={"from_account_id": account_id},
                limit=100
            )
            
            # Combine transactions (this is simplified - in production you'd want proper date filtering)
            all_transactions = incoming_transactions["data"] + outgoing_transactions["data"]
            
            print(f"Found {len(all_transactions)} transactions for account {account_id}")

            # Calculate opening and closing balances (simplified)
            opening_balance = account.balance  # This should be calculated based on transactions before start_date
            closing_balance = account.balance  # This should be calculated based on transactions up to end_date

            return {
                "account_id": account.id,
                "account_number": account.account_number,
                "start_date": start_dt,
                "end_date": end_dt,
                "opening_balance": opening_balance,
                "closing_balance": closing_balance,
                "transactions": all_transactions
            }
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error retrieving statement for account {account_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving statement: {str(e)}"
            )


account_router = AccountRouter()