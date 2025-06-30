#!/usr/bin/env python3
"""
Example scripts demonstrating BaseCRUD methods with practical use cases.
These examples show how to use different BaseCRUD features in real scenarios.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

# Add the app directory to the path
sys.path.append(".")

from app.models.user import User, UserRole
from app.models.account import Account, AccountType, AccountStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.crud.base_crud import BaseCRUD
from app.db.session import get_async_session
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.account import AccountCreate, AccountUpdate
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.core.security import get_password_hash


class CRUDExamples:
    """Examples of BaseCRUD usage"""

    def __init__(self):
        self.user_crud = BaseCRUD(User)
        self.account_crud = BaseCRUD(Account)
        self.transaction_crud = BaseCRUD(Transaction)

    async def run_all_examples(self):
        """Run all CRUD examples"""
        print("🚀 Running BaseCRUD Examples...")

        async for db in get_async_session():
            try:
                await self.example_basic_operations(db)
                await self.example_filtering_and_search(db)
                await self.example_relationships(db)
                await self.example_aggregations(db)
                await self.example_bulk_operations(db)
                await self.example_advanced_queries(db)

            except Exception as e:
                print(f"❌ Example failed: {e}")
                await db.rollback()
                raise
            finally:
                await db.close()

    async def example_basic_operations(self, db):
        """Example 1: Basic CRUD operations"""
        print("\n📝 Example 1: Basic CRUD Operations")
        print("-" * 40)

        # Create a new user
        user_data = UserCreate(
            email="example@test.com",
            first_name="Example",
            last_name="User",
            phone_number="+1234567890",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )

        user = await self.user_crud.create(db, obj_in=user_data)
        print(f"✅ Created user: {user.email}")

        # Get user by ID
        retrieved_user = await self.user_crud.get(db, user.id)
        print(f"✅ Retrieved user: {retrieved_user.email}")

        # Update user
        update_data = {"first_name": "Updated"}
        updated_user = await self.user_crud.update(db, db_obj=user, obj_in=update_data)
        print(f"✅ Updated user: {updated_user.first_name}")

        # Check if user exists
        exists = await self.user_crud.exists(db, email="example@test.com")
        print(f"✅ User exists: {exists}")

        # Count users
        count = await self.user_crud.count(db)
        print(f"✅ Total users: {count}")

        # Clean up
        await self.user_crud.delete(db, id=user.id)
        print("✅ Deleted test user")

    async def example_filtering_and_search(self, db):
        """Example 2: Filtering and search operations"""
        print("\n🔍 Example 2: Filtering and Search")
        print("-" * 40)

        # Create test users
        users_data = [
            UserCreate(
                email="customer1@test.com",
                first_name="Customer",
                last_name="One",
                phone_number="+1111111111",
                hashed_password=get_password_hash("password123"),
                role=UserRole.CUSTOMER,
                is_active=True,
            ),
            UserCreate(
                email="admin1@test.com",
                first_name="Admin",
                last_name="One",
                phone_number="+2222222222",
                hashed_password=get_password_hash("password123"),
                role=UserRole.ADMIN,
                is_active=True,
            ),
            UserCreate(
                email="customer2@test.com",
                first_name="Customer",
                last_name="Two",
                phone_number="+3333333333",
                hashed_password=get_password_hash("password123"),
                role=UserRole.CUSTOMER,
                is_active=False,
            ),
        ]

        users = []
        for user_data in users_data:
            user = await self.user_crud.create(db, obj_in=user_data)
            users.append(user)

        # Filter active customers
        active_customers = await self.user_crud.filter(
            db, filters={"role": UserRole.CUSTOMER, "is_active": True}, limit=10
        )
        print(f"✅ Active customers: {len(active_customers['data'])}")

        # Get users with pagination
        paginated_users = await self.user_crud.filter(
            db, limit=2, skip=0, order_by=["first_name"]
        )
        print(f"✅ Paginated users: {len(paginated_users['data'])}")

        # Get specific fields only
        user_fields = await self.user_crud.filter(
            db, fields=[User.email, User.first_name], limit=5
        )
        print(f"✅ Users with specific fields: {len(user_fields['data'])}")

        # Clean up
        for user in users:
            await self.user_crud.delete(db, id=user.id)
        print("✅ Cleaned up test users")

    async def example_relationships(self, db):
        """Example 3: Working with relationships"""
        print("\n🔗 Example 3: Relationships")
        print("-" * 40)

        # Create a user with accounts
        user_data = UserCreate(
            email="bankuser@test.com",
            first_name="Bank",
            last_name="User",
            phone_number="+4444444444",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        user = await self.user_crud.create(db, obj_in=user_data)

        # Create accounts for the user
        accounts_data = [
            AccountCreate(
                user_id=user.id,
                account_number="ACC001",
                account_type=AccountType.CHECKING,
                balance=Decimal("5000.00"),
                currency="USD",
                status=AccountStatus.ACTIVE,
                overdraft_limit=Decimal("1000.00"),
            ),
            AccountCreate(
                user_id=user.id,
                account_number="ACC002",
                account_type=AccountType.SAVINGS,
                balance=Decimal("15000.00"),
                currency="USD",
                status=AccountStatus.ACTIVE,
                interest_rate=Decimal("0.0250"),
            ),
        ]

        accounts = []
        for account_data in accounts_data:
            account = await self.account_crud.create(db, obj_in=account_data)
            accounts.append(account)

        # Get user with accounts loaded
        user_with_accounts = await self.user_crud.get(
            db, user.id, joins=[User.accounts]
        )
        print(f"✅ User with {len(user_with_accounts.accounts)} accounts")

        # Get related accounts
        user_accounts = await self.user_crud.get_related(db, user.id, "accounts")
        print(f"✅ Related accounts: {len(user_accounts)}")

        # Create transactions
        transaction_data = TransactionCreate(
            from_account_id=None,
            to_account_id=accounts[0].id,
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("1000.00"),
            currency="USD",
            description="Example deposit",
            reference_number="TXN001",
            status=TransactionStatus.COMPLETED,
        )
        transaction = await self.transaction_crud.create(db, obj_in=transaction_data)

        # Get account with transactions
        account_with_transactions = await self.account_crud.get(
            db, accounts[0].id, joins=[Account.to_transactions]
        )
        print(
            f"✅ Account with {len(account_with_transactions.to_transactions)} transactions"
        )

        # Clean up
        await self.transaction_crud.delete(db, id=transaction.id)
        for account in accounts:
            await self.account_crud.delete(db, id=account.id)
        await self.user_crud.delete(db, id=user.id)
        print("✅ Cleaned up test data")

    async def example_aggregations(self, db):
        """Example 4: Aggregation operations"""
        print("\n📊 Example 4: Aggregations")
        print("-" * 40)

        # Create test accounts with different balances
        user_data = UserCreate(
            email="agguser@test.com",
            first_name="Aggregation",
            last_name="User",
            phone_number="+5555555555",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        user = await self.user_crud.create(db, obj_in=user_data)

        accounts_data = [
            AccountCreate(
                user_id=user.id,
                account_number="AGG001",
                account_type=AccountType.CHECKING,
                balance=Decimal("1000.00"),
                currency="USD",
                status=AccountStatus.ACTIVE,
            ),
            AccountCreate(
                user_id=user.id,
                account_number="AGG002",
                account_type=AccountType.SAVINGS,
                balance=Decimal("5000.00"),
                currency="USD",
                status=AccountStatus.ACTIVE,
            ),
            AccountCreate(
                user_id=user.id,
                account_number="AGG003",
                account_type=AccountType.CHECKING,
                balance=Decimal("3000.00"),
                currency="USD",
                status=AccountStatus.ACTIVE,
            ),
        ]

        for account_data in accounts_data:
            await self.account_crud.create(db, obj_in=account_data)

        # Calculate total balance
        total_balance = await self.account_crud.aggregate(db, "balance", "sum")
        print(f"✅ Total balance: ${total_balance}")

        # Find maximum balance
        max_balance = await self.account_crud.aggregate(db, "balance", "max")
        print(f"✅ Maximum balance: ${max_balance}")

        # Calculate average balance
        avg_balance = await self.account_crud.aggregate(db, "balance", "avg")
        print(f"✅ Average balance: ${avg_balance}")

        # Count accounts
        account_count = await self.account_crud.count(db)
        print(f"✅ Total accounts: {account_count}")

        # Clean up
        accounts = await self.account_crud.all(db, limit=10)
        for account in accounts["data"]:
            if account.user_id == user.id:
                await self.account_crud.delete(db, id=account.id)
        await self.user_crud.delete(db, id=user.id)
        print("✅ Cleaned up test data")

    async def example_bulk_operations(self, db):
        """Example 5: Bulk operations"""
        print("\n📦 Example 5: Bulk Operations")
        print("-" * 40)

        # Create multiple users at once
        users_data = [
            UserCreate(
                email="bulk1@test.com",
                first_name="Bulk",
                last_name="User1",
                phone_number="+6666666666",
                hashed_password=get_password_hash("password123"),
                is_active=True,
            ),
            UserCreate(
                email="bulk2@test.com",
                first_name="Bulk",
                last_name="User2",
                phone_number="+7777777777",
                hashed_password=get_password_hash("password123"),
                is_active=True,
            ),
            UserCreate(
                email="bulk3@test.com",
                first_name="Bulk",
                last_name="User3",
                phone_number="+8888888888",
                hashed_password=get_password_hash("password123"),
                is_active=True,
            ),
        ]

        users = await self.user_crud.create_many(db, objs_in=users_data)
        print(f"✅ Created {len(users)} users in bulk")

        # Update multiple users
        for user in users:
            user.first_name = f"Updated_{user.first_name}"
        await self.user_crud.update_many(db, users)
        print("✅ Updated all users in bulk")

        # Delete multiple users
        user_ids = [user.id for user in users]
        await self.user_crud.delete_many(db, user_ids)
        print("✅ Deleted all users in bulk")

    async def example_advanced_queries(self, db):
        """Example 6: Advanced query patterns"""
        print("\n⚡ Example 6: Advanced Queries")
        print("-" * 40)

        # Create test data
        user_data = UserCreate(
            email="advanced@test.com",
            first_name="Advanced",
            last_name="User",
            phone_number="+9999999999",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        user = await self.user_crud.create(db, obj_in=user_data)

        # Create accounts with different statuses
        accounts_data = [
            AccountCreate(
                user_id=user.id,
                account_number="ADV001",
                account_type=AccountType.CHECKING,
                balance=Decimal("1000.00"),
                currency="USD",
                status=AccountStatus.ACTIVE,
            ),
            AccountCreate(
                user_id=user.id,
                account_number="ADV002",
                account_type=AccountType.SAVINGS,
                balance=Decimal("5000.00"),
                currency="USD",
                status=AccountStatus.FROZEN,
            ),
        ]

        accounts = []
        for account_data in accounts_data:
            account = await self.account_crud.create(db, obj_in=account_data)
            accounts.append(account)

        # Get user with specific fields and joins
        user_with_accounts = await self.user_crud.get(
            db, user.id, fields=[User.email, User.first_name], joins=[User.accounts]
        )
        print(f"✅ User with specific fields and joins: {user_with_accounts.email}")

        # Filter accounts by type and status
        active_checking = await self.account_crud.filter(
            db,
            filters={
                "account_type": AccountType.CHECKING,
                "status": AccountStatus.ACTIVE,
            },
        )
        print(f"✅ Active checking accounts: {len(active_checking['data'])}")

        # Get accounts ordered by balance
        ordered_accounts = await self.account_crud.filter(
            db, order_by=["-balance"], limit=5
        )
        print(f"✅ Accounts ordered by balance: {len(ordered_accounts['data'])}")

        # Clean up
        for account in accounts:
            await self.account_crud.delete(db, id=account.id)
        await self.user_crud.delete(db, id=user.id)
        print("✅ Cleaned up test data")


async def main():
    """Main function"""
    examples = CRUDExamples()
    await examples.run_all_examples()
    print("\n🎉 All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
