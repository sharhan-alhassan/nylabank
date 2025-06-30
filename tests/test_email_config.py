#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.asyncio

"""
Test email configuration
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.utility import conf


async def test_email_config():
    """Test email configuration"""
    print("🧪 Testing Email Configuration")
    print("=" * 50)
    
    print(f"MAIL_SERVER: {settings.MAIL_SERVER}")
    print(f"MAIL_PORT: {settings.MAIL_PORT}")
    print(f"MAIL_USERNAME: {settings.MAIL_USERNAME}")
    print(f"MAIL_FROM: {settings.MAIL_FROM}")
    print(f"MAIL_FROM_NAME: {settings.MAIL_FROM_NAME}")
    print(f"MAIL_STARTTLS: {settings.MAIL_STARTTLS}")
    print(f"MAIL_SSL_TLS: {settings.MAIL_SSL_TLS}")
    print(f"USE_CREDENTIALS: {settings.USE_CREDENTIALS}")
    print(f"VALIDATE_CERTS: {settings.VALIDATE_CERTS}")
    
    print("\n" + "=" * 50)
    print("📧 Connection Configuration:")
    print(f"conf.MAIL_SERVER: {conf.MAIL_SERVER}")
    print(f"conf.MAIL_PORT: {conf.MAIL_PORT}")
    print(f"conf.MAIL_USERNAME: {conf.MAIL_USERNAME}")
    print(f"conf.MAIL_FROM: {conf.MAIL_FROM}")
    print(f"conf.MAIL_FROM_NAME: {conf.MAIL_FROM_NAME}")
    print(f"conf.MAIL_STARTTLS: {conf.MAIL_STARTTLS}")
    print(f"conf.MAIL_SSL_TLS: {conf.MAIL_SSL_TLS}")
    print(f"conf.USE_CREDENTIALS: {conf.USE_CREDENTIALS}")
    
    # Check for missing values
    missing_values = []
    if not settings.MAIL_USERNAME:
        missing_values.append("MAIL_USERNAME")
    if not settings.MAIL_PASSWORD:
        missing_values.append("MAIL_PASSWORD")
    if not settings.MAIL_FROM:
        missing_values.append("MAIL_FROM")
    if not settings.MAIL_SERVER:
        missing_values.append("MAIL_SERVER")
    
    if missing_values:
        print(f"\n❌ Missing email configuration: {', '.join(missing_values)}")
        return False
    else:
        print("\n✅ Email configuration looks good!")
        return True


if __name__ == "__main__":
    asyncio.run(test_email_config()) 