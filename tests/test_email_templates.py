#!/usr/bin/env python3
import pytest

pytestmark = pytest.mark.asyncio

"""
Test script for email template functions
Run this script to test all email template functions
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utility import (
    send_email_verification_code,
    send_password_reset_email,
    send_transaction_notification,
    send_welcome_email,
    render_registration_verification_email,
    render_transaction_notification_email,
)
from datetime import datetime


async def test_email_verification():
    """Test email verification template"""
    print("Testing email verification template...")
    try:
        await send_email_verification_code(
            {"verify_code": "123456", "email_to": "test@example.com"}
        )
        print("✅ Email verification template test passed")
    except Exception as e:
        print(f"❌ Email verification template test failed: {e}")


async def test_password_reset():
    """Test password reset template"""
    print("Testing password reset template...")
    try:
        await send_password_reset_email(
            {"reset_code": "789012", "email_to": "test@example.com"}
        )
        print("✅ Password reset template test passed")
    except Exception as e:
        print(f"❌ Password reset template test failed: {e}")


async def test_transaction_notification():
    """Test transaction notification template"""
    print("Testing transaction notification template...")
    try:
        await send_transaction_notification(
            {
                "email_to": "test@example.com",
                "transaction_type": "DEPOSIT",
                "reference_number": "DEP123456789ABC",
                "amount": "1000.00",
                "currency": "USD",
                "account_number": "1234567890",
                "balance_after": "5000.00",
                "transaction_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                "description": "Test deposit",
            }
        )
        print("✅ Transaction notification template test passed")
    except Exception as e:
        print(f"❌ Transaction notification template test failed: {e}")


async def test_welcome_email():
    """Test welcome email template"""
    print("Testing welcome email template...")
    try:
        await send_welcome_email(
            {
                "email_to": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "account_type": "CUSTOMER",
                "join_date": datetime.now().strftime("%B %d, %Y"),
            }
        )
        print("✅ Welcome email template test passed")
    except Exception as e:
        print(f"❌ Welcome email template test failed: {e}")


async def test_transfer_notification():
    """Test transfer notification template"""
    print("Testing transfer notification template...")
    try:
        await send_transaction_notification(
            {
                "email_to": "test@example.com",
                "transaction_type": "TRANSFER",
                "reference_number": "TRF987654321XYZ",
                "amount": "500.00",
                "currency": "USD",
                "account_number": "1234567890",
                "balance_after": "4500.00",
                "transaction_date": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                "description": "Transfer to savings",
                "from_account_last4": "7890",
                "to_account_last4": "1234",
            }
        )
        print("✅ Transfer notification template test passed")
    except Exception as e:
        print(f"❌ Transfer notification template test failed: {e}")


def test_registration_verification_email_content():
    html = render_registration_verification_email(name="Sharhan", verify_code="123456")
    assert "Hi Sharhan" in html
    assert "123456" in html
    assert "verification code" in html


def test_transaction_notification_email_content():
    html = render_transaction_notification_email(
        name="Sharhan",
        transaction_type="DEPOSIT",
        reference_number="TXN123",
        amount="100.00",
        currency="USD",
        account_number="ACC001",
        balance_after="1100.00",
        transaction_date="June 30, 2025",
        description="Test deposit",
        from_account_last4="0001",
        to_account_last4="0002",
        dashboard_url="https://nylabankapi.prod.maoney.co/dashboard",
    )
    assert "Sharhan" in html
    assert "Deposit" in html or "deposit" in html
    assert "TXN123" in html
    assert "100.00" in html
    assert "USD" in html
    assert "ACC001" in html
    assert "1100.00" in html
    assert "Test deposit" in html
    assert "dashboard" in html
    # Only check for account last4 if transaction_type is TRANSFER
    if "Transfer" in html or "transfer" in html:
        assert "0001" in html
        assert "0002" in html


async def main():
    """Run all email template tests"""
    print("🧪 Testing Email Templates")
    print("=" * 50)

    # Test all email templates
    await test_email_verification()
    await test_password_reset()
    await test_transaction_notification()
    await test_welcome_email()
    await test_transfer_notification()

    print("\n" + "=" * 50)
    print("🎉 Email template testing completed!")
    print(
        "\nNote: Check your email configuration in settings to ensure emails are actually sent."
    )
    print("If emails are not being sent, check your SMTP settings in the config file.")


if __name__ == "__main__":
    asyncio.run(main())
