#!/usr/bin/env python3
import pytest
pytestmark = pytest.mark.asyncio

"""
Test real email sending
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utility import send_email_verification_code


async def test_real_email():
    """Test sending a real email"""
    print("🧪 Testing Real Email Sending")
    print("=" * 50)
    
    try:
        await send_email_verification_code({
            "verify_code": "123456",
            "email_to": "test@example.com"  # Change this to your email for testing
        })
        print("✅ Email sent successfully!")
        print("Check your email inbox (and spam folder) for the test email.")
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Print more detailed error information
        import traceback
        print("\nFull error traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_real_email()) 