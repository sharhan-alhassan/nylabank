#!/usr/bin/env python3
"""
Simple seed data script for creating and deleting test data.
Usage: python scripts/seed_data.py [create|delete]
"""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add the app directory to the path
sys.path.append(".")

from app.models.user import User, UserRole
from app.models.account import Account, AccountType, AccountStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.otp import Otp
from app.crud.base_crud import BaseCRUD
from app.db.session import get_async_session
from app.schemas.user import UserCreate
from app.schemas.account import AccountCreate
from app.schemas.transaction import TransactionCreate
from app.schemas.otp import OtpCreate
from app.core.security import get_password_hash


class DataSeeder:
    """Simple data seeder for testing"""

    def __init__(self):
        self.created_data = {
            "users": [],
            "accounts": [],
            "transactions": [],
            "otps": [],
        }

    async def create_sample_data(self, db):
        """Create sample data for testing"""
        print("🌱 Creating sample data...")

        # Create users
        users = await self._create_users(db)
        print(f"✅ Created {len(users)} users")

        # Create accounts
        accounts = await self._create_accounts(db, users)
        print(f"✅ Created {len(accounts)} accounts")

        # Create transactions
        transactions = await self._create_transactions(db, accounts)
        print(f"✅ Created {len(transactions)} transactions")

        # Create OTPs
        otps = await self._create_otps(db)
        print(f"✅ Created {len(otps)} OTPs")

        print("🎉 Sample data created successfully!")
        return users, accounts, transactions, otps

    async def _create_users(self, db):
        """Create sample users"""
        user_crud = BaseCRUD(User)

        users_data = [
            {
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Johnson",
                "phone_number": "+1234567890",
                "date_of_birth": datetime(1990, 1, 15),
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip_code": "10001",
                    "country": "USA",
                },
                "role": UserRole.CUSTOMER,
                "is_active": True,
                "hashed_password": get_password_hash("password123"),
            },
            {
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Smith",
                "phone_number": "+1987654321",
                "date_of_birth": datetime(1985, 5, 20),
                "address": {
                    "street": "456 Oak Ave",
                    "city": "Los Angeles",
                    "state": "CA",
                    "zip_code": "90210",
                    "country": "USA",
                },
                "role": UserRole.ADMIN,
                "is_active": True,
                "hashed_password": get_password_hash("password456"),
            },
        ]

        users = []
        for user_data in users_data:
            user_schema = UserCreate(**user_data)
            user = await user_crud.create(db, obj_in=user_schema)
            users.append(user)
            self.created_data["users"].append(user)

        return users

    async def _create_accounts(self, db, users):
        """Create sample accounts"""
        account_crud = BaseCRUD(Account)

        accounts_data = [
            {
                "user_id": users[0].id,
                "account_number": "ACC001",
                "account_type": AccountType.CHECKING,
                "balance": Decimal("5000.00"),
                "currency": "USD",
                "status": AccountStatus.ACTIVE,
                "overdraft_limit": Decimal("1000.00"),
                "interest_rate": None,
            },
            {
                "user_id": users[0].id,
                "account_number": "ACC002",
                "account_type": AccountType.SAVINGS,
                "balance": Decimal("15000.00"),
                "currency": "USD",
                "status": AccountStatus.ACTIVE,
                "overdraft_limit": Decimal("0.00"),
                "interest_rate": Decimal("0.0250"),
            },
            {
                "user_id": users[1].id,
                "account_number": "ACC003",
                "account_type": AccountType.CHECKING,
                "balance": Decimal("25000.00"),
                "currency": "USD",
                "status": AccountStatus.ACTIVE,
                "overdraft_limit": Decimal("5000.00"),
                "interest_rate": None,
            },
        ]

        accounts = []
        for account_data in accounts_data:
            account_schema = AccountCreate(**account_data)
            account = await account_crud.create(db, obj_in=account_schema)
            accounts.append(account)
            self.created_data["accounts"].append(account)

        return accounts

    async def _create_transactions(self, db, accounts):
        """Create sample transactions"""
        transaction_crud = BaseCRUD(Transaction)

        transactions_data = [
            {
                "from_account_id": None,
                "to_account_id": accounts[0].id,
                "transaction_type": TransactionType.DEPOSIT,
                "amount": Decimal("1000.00"),
                "currency": "USD",
                "description": "Initial deposit",
                "reference_number": "TXN001",
                "status": TransactionStatus.COMPLETED,
                "balance_after": Decimal("6000.00"),
                "transaction_metadata": {"source": "cash_deposit"},
                "processed_at": datetime.now(),
            },
            {
                "from_account_id": accounts[0].id,
                "to_account_id": accounts[1].id,
                "transaction_type": TransactionType.TRANSFER,
                "amount": Decimal("500.00"),
                "currency": "USD",
                "description": "Transfer to savings",
                "reference_number": "TXN002",
                "status": TransactionStatus.COMPLETED,
                "balance_after": Decimal("5500.00"),
                "transaction_metadata": {"transfer_type": "internal"},
                "processed_at": datetime.now(),
            },
        ]

        transactions = []
        for transaction_data in transactions_data:
            transaction_schema = TransactionCreate(**transaction_data)
            transaction = await transaction_crud.create(db, obj_in=transaction_schema)
            transactions.append(transaction)
            self.created_data["transactions"].append(transaction)

        return transactions

    async def _create_otps(self, db):
        """Create sample OTPs"""
        otp_crud = BaseCRUD(Otp)

        otps_data = [
            {
                "email": "alice@example.com",
                "otp_code": "123456",
                "expires_on": datetime.now() + timedelta(minutes=10),
                "is_expired": False,
            },
            {
                "email": "bob@example.com",
                "otp_code": "654321",
                "expires_on": datetime.now() - timedelta(minutes=5),
                "is_expired": True,
            },
        ]

        otps = []
        for otp_data in otps_data:
            otp_schema = OtpCreate(**otp_data)
            otp = await otp_crud.create(db, obj_in=otp_schema)
            otps.append(otp)
            self.created_data["otps"].append(otp)

        return otps

    async def delete_all_data(self, db):
        """Delete all created data"""
        print("🧹 Deleting all data...")

        # Delete in reverse order to respect foreign key constraints
        for transaction in self.created_data["transactions"]:
            await db.delete(transaction)

        for account in self.created_data["accounts"]:
            await db.delete(account)

        for otp in self.created_data["otps"]:
            await db.delete(otp)

        for user in self.created_data["users"]:
            await db.delete(user)

        await db.commit()
        print("✅ All data deleted successfully!")

        # Clear the lists
        self.created_data = {
            "users": [],
            "accounts": [],
            "transactions": [],
            "otps": [],
        }


async def main():
    """Main function"""
    if len(sys.argv) != 2 or sys.argv[1] not in ["create", "delete"]:
        print("Usage: python scripts/seed_data.py [create|delete]")
        sys.exit(1)

    action = sys.argv[1]
    seeder = DataSeeder()

    async for db in get_async_session():
        try:
            if action == "create":
                await seeder.create_sample_data(db)
            elif action == "delete":
                await seeder.delete_all_data(db)
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()


if __name__ == "__main__":
    asyncio.run(main())
