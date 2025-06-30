#!/usr/bin/env python3
import pytest

pytestmark = pytest.mark.asyncio

"""
Debug email API functionality
"""

import asyncio
import sys
import os
from fastapi.testclient import TestClient
from main import app

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utility import send_email_verification_code, conf
from app.config import settings
from app.utilities.logger import logger

client = TestClient(app)


async def debug_email_api():
    """Debug email API functionality"""
    print("🔍 Debugging Email API Functionality")
    print("=" * 50)

    # Print configuration
    print("📧 Email Configuration:")
    print(f"MAIL_SERVER: {settings.MAIL_SERVER}")
    print(f"MAIL_PORT: {settings.MAIL_PORT}")
    print(f"MAIL_USERNAME: {settings.MAIL_USERNAME}")
    print(f"MAIL_FROM: {settings.MAIL_FROM}")
    print(f"MAIL_FROM_NAME: {settings.MAIL_FROM_NAME}")
    print(f"MAIL_STARTTLS: {settings.MAIL_STARTTLS}")
    print(f"MAIL_SSL_TLS: {settings.MAIL_SSL_TLS}")
    print(f"USE_CREDENTIALS: {settings.USE_CREDENTIALS}")

    print("\n📧 Connection Configuration:")
    print(f"conf.MAIL_SERVER: {conf.MAIL_SERVER}")
    print(f"conf.MAIL_PORT: {conf.MAIL_PORT}")
    print(f"conf.MAIL_USERNAME: {conf.MAIL_USERNAME}")
    print(f"conf.MAIL_FROM: {conf.MAIL_FROM}")
    print(f"conf.MAIL_FROM_NAME: {conf.MAIL_FROM_NAME}")
    print(f"conf.MAIL_STARTTLS: {conf.MAIL_STARTTLS}")
    print(f"conf.MAIL_SSL_TLS: {conf.MAIL_SSL_TLS}")
    print(f"conf.USE_CREDENTIALS: {conf.USE_CREDENTIALS}")

    print("\n🧪 Testing Email Sending...")

    try:
        await send_email_verification_code(
            {"verify_code": "123456", "email_to": "test@example.com"}
        )
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")

        # Print more detailed error information
        import traceback

        print("\nFull error traceback:")
        traceback.print_exc()

        # Log the error
        logger.error(f"Email sending failed: {str(e)}")


def test_unauthorized_access():
    # Try to access a protected endpoint without auth
    response = client.get("/api/v1/accounts/")
    assert response.status_code in (401, 403)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    asyncio.run(debug_email_api())
