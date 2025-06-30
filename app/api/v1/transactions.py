from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
from app.crud.transaction import transaction_crud
from app.crud.accounts import account_crud
from app.crud.users import user_crud
from app.db.session import get_async_session
from app.schemas.transaction import (
    Transaction,
    TransactionCreate,
    DepositRequest,
    WithdrawRequest,
    TransferRequest,
    TransactionList,
    TransactionCreateResponse,
    TransactionReverseRequest,
    TransactionReverseResponse,
)
from app.core.deps import get_current_user, get_current_admin
from app.models.user import UserRole, User
from app.models.transaction import TransactionType, TransactionStatus
from app.models.account import AccountStatus
from app.utility import send_transaction_notification
from app.utilities.logger import logger
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import uuid
import random
import string


def generate_reference_number(transaction_type: str) -> str:
    """Generate a unique reference number for transactions"""
    # Generate 12 random alphanumeric characters
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    # Prefix based on transaction type
    prefix = {
        "deposit": "DEP",
        "withdrawal": "WTH", 
        "transfer": "TRF",
        "reversal": "REV"
    }.get(transaction_type.lower(), "TXN")
    
    return f"{prefix}{random_chars}"


class TransactionRouter:
    def __init__(self):
        self.router = APIRouter()
        self.prefix = "/transactions"
        self.tags = ["transactions"]
        self.singular = "transaction"
        self.plural = "transactions"

        self.router.add_api_route(
            "/deposit",
            self.deposit,
            methods=["POST"],
            response_model=TransactionCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Deposit money into account",
        )

        self.router.add_api_route(
            "/withdraw",
            self.withdraw,
            methods=["POST"],
            response_model=TransactionCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Withdraw money from account",
        )

        self.router.add_api_route(
            "/transfer",
            self.transfer,
            methods=["POST"],
            response_model=TransactionCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Transfer money",
        )

        self.router.add_api_route(
            "/",
            self.list_transactions,
            methods=["GET"],
            response_model=TransactionList,
            summary="List transactions",
        )

        self.router.add_api_route(
            "/{transaction_id}",
            self.get_transaction,
            methods=["GET"],
            response_model=Transaction,
            summary="Get transaction details",
        )

        self.router.add_api_route(
            "/{transaction_id}/reverse",
            self.reverse_transaction,
            methods=["POST"],
            response_model=TransactionReverseResponse,
            summary="Reverse transaction (admin only)",
        )

    async def deposit(
        self,
        deposit_in: DepositRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Deposit money into account"""
        try:
            # Get the account
            account = await account_crud.get_or_404(db, deposit_in.account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            # Check if account is active
            if account.status != AccountStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account is not active"
                )

            # Generate reference number
            reference_number = generate_reference_number("deposit")

            # Calculate new balance
            new_balance = account.balance + deposit_in.amount

            # Create transaction data with balance_after
            transaction_data = TransactionCreate(
                from_account_id=None,
                to_account_id=account.id,
                transaction_type=TransactionType.DEPOSIT,
                amount=deposit_in.amount,
                currency=account.currency,
                description=deposit_in.description or "Deposit",
                reference_number=reference_number,
                status=TransactionStatus.COMPLETED,
                balance_after=new_balance,  # Track balance after transaction
                processed_at=datetime.now()
            )

            transaction = await transaction_crud.create(db, obj_in=transaction_data)

            # Update account balance
            await account_crud.update(
                db,
                db_obj=account,
                obj_in={"balance": new_balance}
            )

            # Send transaction notification
            async def send_notification_task():
                try:
                    # Get user for email
                    user = await user_crud.get(db, account.user_id)
                    if user and user.email:
                        await send_transaction_notification({
                            "email_to": user.email,
                            "transaction_type": "DEPOSIT",
                            "reference_number": reference_number,
                            "amount": str(deposit_in.amount),
                            "currency": account.currency,
                            "account_number": account.account_number,
                            "balance_after": str(new_balance),
                            "transaction_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                            "description": deposit_in.description or "Deposit",
                            "name": user.first_name.title(),
                        })
                        logger.info(f"Transaction notification sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send transaction notification: {str(e)}")

            background_tasks.add_task(send_notification_task)

            return {
                "detail": f"Deposit of {deposit_in.amount} {account.currency} completed successfully",
                "transaction": transaction
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing deposit: {str(e)}"
            )

    async def withdraw(
        self,
        withdraw_in: WithdrawRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Withdraw money from account"""
        try:
            # Get the account
            account = await account_crud.get_or_404(db, withdraw_in.account_id)

            # Check if user has access to this account
            if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this account"
                )

            # Check if account is active
            if account.status != AccountStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account is not active"
                )

            # Check if sufficient balance
            if account.balance < withdraw_in.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance"
                )

            # Generate reference number
            reference_number = generate_reference_number("withdrawal")

            # Calculate new balance
            new_balance = account.balance - withdraw_in.amount

            # Create transaction with balance_after
            transaction_data = TransactionCreate(
                from_account_id=account.id,
                to_account_id=None,
                transaction_type=TransactionType.WITHDRAWAL,
                amount=withdraw_in.amount,
                currency=account.currency,
                description=withdraw_in.description or "Withdrawal",
                reference_number=reference_number,
                status=TransactionStatus.COMPLETED,
                balance_after=new_balance,  # Track balance after transaction
                processed_at=datetime.now()
            )

            transaction = await transaction_crud.create(db, obj_in=transaction_data)

            # Update account balance
            await account_crud.update(
                db,
                db_obj=account,
                obj_in={"balance": new_balance}
            )

            # Send transaction notification
            async def send_notification_task():
                try:
                    # Get user for email
                    user = await user_crud.get(db, account.user_id)
                    if user and user.email:
                        await send_transaction_notification({
                            "email_to": user.email,
                            "transaction_type": "WITHDRAWAL",
                            "reference_number": reference_number,
                            "amount": str(withdraw_in.amount),
                            "currency": account.currency,
                            "account_number": account.account_number,
                            "balance_after": str(new_balance),
                            "transaction_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                            "description": withdraw_in.description or "Withdrawal",
                            "name": user.first_name.title(),
                        })
                        logger.info(f"Transaction notification sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send transaction notification: {str(e)}")

            background_tasks.add_task(send_notification_task)

            return {
                "detail": f"Withdrawal of {withdraw_in.amount} {account.currency} completed successfully",
                "transaction": transaction
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing withdrawal: {str(e)}"
            )

    async def transfer(
        self,
        transfer_in: TransferRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Transfer money between accounts"""
        try:
            # Get the accounts
            from_account = await account_crud.get_or_404(db, transfer_in.from_account_id)
            to_account = await account_crud.get_or_404(db, transfer_in.to_account_id)

            # Check if user has access to the from_account
            if current_user.role == UserRole.CUSTOMER and from_account.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to source account"
                )

            # Check if accounts are active
            if from_account.status != AccountStatus.ACTIVE or to_account.status != AccountStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or both accounts are not active"
                )

            # Check if sufficient balance in source account
            if from_account.balance < transfer_in.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance in source account"
                )

            # Check if accounts have same currency
            if from_account.currency != to_account.currency:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot transfer between accounts with different currencies"
                )

            # Generate reference number
            reference_number = generate_reference_number("transfer")

            # Calculate new balances
            from_new_balance = from_account.balance - transfer_in.amount
            to_new_balance = to_account.balance + transfer_in.amount

            # Create transaction with balance_after (for the from_account)
            transaction_data = TransactionCreate(
                from_account_id=from_account.id,
                to_account_id=to_account.id,
                transaction_type=TransactionType.TRANSFER,
                amount=transfer_in.amount,
                currency=from_account.currency,
                description=transfer_in.description or "Transfer",
                reference_number=reference_number,
                status=TransactionStatus.COMPLETED,
                balance_after=from_new_balance,  # Track balance after transaction for source account
                processed_at=datetime.now()
            )

            transaction = await transaction_crud.create(db, obj_in=transaction_data)

            # Update account balances
            await account_crud.update(
                db,
                db_obj=from_account,
                obj_in={"balance": from_new_balance}
            )
            await account_crud.update(
                db,
                db_obj=to_account,
                obj_in={"balance": to_new_balance}
            )

            # Send transaction notifications
            async def send_notification_task():
                try:
                    # Get users for email notifications
                    from_user = await user_crud.get(db, from_account.user_id)
                    to_user = await user_crud.get(db, to_account.user_id)
                    
                    # Send notification to sender
                    if from_user and from_user.email:
                        await send_transaction_notification({
                            "email_to": from_user.email,
                            "transaction_type": "TRANSFER",
                            "reference_number": reference_number,
                            "amount": str(transfer_in.amount),
                            "currency": from_account.currency,
                            "account_number": from_account.account_number,
                            "balance_after": str(from_new_balance),
                            "transaction_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                            "description": transfer_in.description or "Transfer",
                            "from_account_last4": from_account.account_number[-4:],
                            "to_account_last4": to_account.account_number[-4:],
                            "name": from_user.first_name.title(),
                        })
                        logger.info(f"Transfer notification sent to sender {from_user.email}")
                    
                    # Send notification to recipient (if different user)
                    if to_user and to_user.email and to_user.id != from_user.id:
                        await send_transaction_notification({
                            "email_to": to_user.email,
                            "transaction_type": "TRANSFER",
                            "reference_number": reference_number,
                            "amount": str(transfer_in.amount),
                            "currency": to_account.currency,
                            "account_number": to_account.account_number,
                            "balance_after": str(to_new_balance),
                            "transaction_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                            "description": f"Received transfer: {transfer_in.description or 'Transfer'}",
                            "from_account_last4": from_account.account_number[-4:],
                            "to_account_last4": to_account.account_number[-4:],
                            "name": to_user.first_name.title(), 
                        })
                        logger.info(f"Transfer notification sent to recipient {to_user.email}")
                except Exception as e:
                    logger.error(f"Failed to send transfer notification: {str(e)}")

            background_tasks.add_task(send_notification_task)

            return {
                "detail": f"Transfer of {transfer_in.amount} {from_account.currency} completed successfully",
                "transaction": transaction
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing transfer: {str(e)}"
            )

    async def list_transactions(
        self,
        account_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 10,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """List transactions with pagination"""
        try:
            # Validate pagination parameters
            if page < 1:
                page = 1
            if per_page < 1 or per_page > 50:
                per_page = 10
            
            skip = (page - 1) * per_page
            
            if account_id:
                # Check if user has access to this specific account
                account = await account_crud.get_or_404(db, account_id)
                if current_user.role == UserRole.CUSTOMER and account.user_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied to this account"
                    )
                
                # Get transactions for this specific account (both incoming and outgoing)
                incoming_transactions = await transaction_crud.filter(
                    db,
                    filters={"to_account_id": account_id},
                    limit=per_page,
                    skip=skip,
                    order_by=["-created_at"]
                )
                
                outgoing_transactions = await transaction_crud.filter(
                    db,
                    filters={"from_account_id": account_id},
                    limit=per_page,
                    skip=skip,
                    order_by=["-created_at"]
                )
                
                # Combine and sort transactions
                all_transactions = incoming_transactions["data"] + outgoing_transactions["data"]
                # Sort by created_at (most recent first)
                all_transactions.sort(key=lambda x: x.created_at, reverse=True)
                
                # Apply pagination manually since we combined results
                start_idx = skip
                end_idx = start_idx + per_page
                paginated_transactions = all_transactions[start_idx:end_idx]
                
                total_count = len(all_transactions)
                
            else:
                # For customers, get transactions for all their accounts
                if current_user.role == UserRole.CUSTOMER:
                    # Get user's accounts
                    user_accounts = await account_crud.filter(
                        db, filters={"user_id": current_user.id}, limit=100
                    )
                    account_ids = [acc.id for acc in user_accounts["data"]]
                    
                    if not account_ids:
                        return {
                            "total_count": 0,
                            "page": page,
                            "per_page": per_page,
                            "total_pages": 0,
                            "data": []
                        }
                    
                    # Get transactions for all user accounts
                    all_transactions = []
                    for acc_id in account_ids:
                        # Get incoming transactions
                        incoming = await transaction_crud.filter(
                            db,
                            filters={"to_account_id": acc_id},
                            limit=1000,  # Get all transactions for this account
                            skip=0
                        )
                        all_transactions.extend(incoming["data"])
                        
                        # Get outgoing transactions
                        outgoing = await transaction_crud.filter(
                            db,
                            filters={"from_account_id": acc_id},
                            limit=1000,  # Get all transactions for this account
                            skip=0
                        )
                        all_transactions.extend(outgoing["data"])
                    
                    # Sort by created_at (most recent first)
                    all_transactions.sort(key=lambda x: x.created_at, reverse=True)
                    
                    # Apply pagination
                    start_idx = skip
                    end_idx = start_idx + per_page
                    paginated_transactions = all_transactions[start_idx:end_idx]
                    
                    total_count = len(all_transactions)
                    
                else:
                    # Admin can see all transactions
                    transactions = await transaction_crud.filter(
                        db,
                        filters={},
                        limit=per_page,
                        skip=skip,
                        order_by=["-created_at"]
                    )
                    paginated_transactions = transactions["data"]
                    total_count = transactions["total_count"]

            # Calculate pagination info
            total_pages = (total_count + per_page - 1) // per_page

            return {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "data": paginated_transactions
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving transactions: {str(e)}"
            )

    async def get_transaction(
        self,
        transaction_id: UUID,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Get transaction details"""
        try:
            transaction = await transaction_crud.get_or_404(db, transaction_id)

            # Check if user has access to this transaction
            if current_user.role == UserRole.CUSTOMER:
                # Check if user owns either the from or to account
                if transaction.from_account_id:
                    from_account = await account_crud.get(db, transaction.from_account_id)
                    if from_account and from_account.user_id == current_user.id:
                        return transaction
                
                if transaction.to_account_id:
                    to_account = await account_crud.get(db, transaction.to_account_id)
                    if to_account and to_account.user_id == current_user.id:
                        return transaction

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this transaction"
                )

            return transaction
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving transaction: {str(e)}"
            )

    async def reverse_transaction(
        self,
        transaction_id: UUID,
        reverse_in: TransactionReverseRequest,
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user),
    ) -> Any:
        """Reverse transaction (admin only)"""
        try:
            # Check if user is admin
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can reverse transactions"
                )

            # Get the original transaction
            original_transaction = await transaction_crud.get_or_404(db, transaction_id)

            # Check if transaction can be reversed
            if original_transaction.status != TransactionStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only completed transactions can be reversed"
                )

            # Create reversal transaction
            reversal_data = TransactionCreate(
                from_account_id=original_transaction.to_account_id,
                to_account_id=original_transaction.from_account_id,
                transaction_type=original_transaction.transaction_type,
                amount=original_transaction.amount,
                currency=original_transaction.currency,
                description=f"Reversal: {original_transaction.description}",
                reference_number=generate_reference_number("reversal"),
                status=TransactionStatus.COMPLETED,
                processed_at=datetime.now(),
                transaction_metadata={
                    "reversed_transaction_id": str(original_transaction.id),
                    "reason": reverse_in.reason
                }
            )

            reversal_transaction = await transaction_crud.create(db, obj_in=reversal_data)

            # Update account balances
            if original_transaction.from_account_id:
                from_account = await account_crud.get(db, original_transaction.from_account_id)
                if from_account:
                    new_balance = from_account.balance + original_transaction.amount
                    # Update reversal transaction with balance_after for from_account
                    await transaction_crud.update(
                        db,
                        db_obj=reversal_transaction,
                        obj_in={"balance_after": new_balance}
                    )
                    await account_crud.update(
                        db,
                        db_obj=from_account,
                        obj_in={"balance": new_balance}
                    )

            if original_transaction.to_account_id:
                to_account = await account_crud.get(db, original_transaction.to_account_id)
                if to_account:
                    new_balance = to_account.balance - original_transaction.amount
                    await account_crud.update(
                        db,
                        db_obj=to_account,
                        obj_in={"balance": new_balance}
                    )

            # Mark original transaction as reversed
            await transaction_crud.update(
                db,
                db_obj=original_transaction,
                obj_in={"status": TransactionStatus.REVERSED}
            )

            return {
                "detail": f"Transaction {original_transaction.reference_number} reversed successfully",
                "original_transaction": original_transaction,
                "reversal_transaction": reversal_transaction
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reversing transaction: {str(e)}"
            )


transaction_router = TransactionRouter()
