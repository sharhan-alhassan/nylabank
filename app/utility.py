import random
from typing import Dict
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.config import settings
from datetime import datetime


TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_DIR.mkdir(exist_ok=True)


def generate_otp_code() -> str:
    return str(random.randint(100000, 999999))


# Custom Jinja2 filters
def date_filter(value, format_str="%Y-%m-%d"):
    """Custom date filter for Jinja2 templates"""
    if isinstance(value, str) and value == "now":
        value = datetime.now()
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except:
            return value

    if isinstance(value, datetime):
        return value.strftime(format_str)
    return str(value)


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    TEMPLATE_FOLDER=TEMPLATE_DIR,
)

template_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
template_env.filters["date"] = date_filter


async def send_email_verification_code(data: Dict):
    """
    Send email verification code for account registration.

    Args:
        data: Dictionary containing email details including:
            - verify_code: The verification code
            - email_to: Recipient's email address
            - name: Recipient's name
    """
    template = template_env.get_template("registration_verification.html")

    context = {
        "verify_code": data["verify_code"],
        "recipient_email": data["email_to"],
        "name": data["name"],
    }

    html_content = template.render(**context)

    message = MessageSchema(
        subject="Account Activation - NylaBank",
        recipients=[data["email_to"]],
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(data: Dict):
    """
    Send password reset verification code.

    Args:
        data: Dictionary containing email details including:
            - reset_code: The password reset code
            - email_to: Recipient's email address
    """
    template = template_env.get_template("password_reset.html")

    context = {
        "reset_code": data["reset_code"],
        "recipient_email": data["email_to"],
    }

    html_content = template.render(**context)

    message = MessageSchema(
        subject="Password Reset - NylaBank",
        recipients=[data["email_to"]],
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_transaction_notification(data: Dict):
    """
    Send transaction completion notification.

    Args:
        data: Dictionary containing transaction details including:
            - email_to: Recipient's email address
            - transaction_type: Type of transaction (DEPOSIT, WITHDRAWAL, TRANSFER)
            - reference_number: Transaction reference number
            - amount: Transaction amount
            - currency: Transaction currency
            - account_number: Account number
            - balance_after: Balance after transaction
            - transaction_date: Date of transaction
            - description: Transaction description (optional)
            - from_account_last4: Last 4 digits of source account (for transfers)
            - to_account_last4: Last 4 digits of destination account (for transfers)
            - dashboard_url: URL to user dashboard
    """
    template = template_env.get_template("transaction_notification.html")

    context = {
        "recipient_email": data["email_to"],
        "transaction_type": data["transaction_type"],
        "reference_number": data["reference_number"],
        "amount": data["amount"],
        "currency": data["currency"],
        "account_number": data["account_number"],
        "balance_after": data["balance_after"],
        "transaction_date": data["transaction_date"],
        "description": data.get("description"),
        "from_account_last4": data.get("from_account_last4"),
        "to_account_last4": data.get("to_account_last4"),
        "dashboard_url": data.get(
            "dashboard_url", "https://app.nylabank.com/dashboard"
        ),
    }

    html_content = template.render(**context)

    message = MessageSchema(
        subject=f"Transaction Completed - {data['transaction_type'].title()} - NylaBank",
        recipients=[data["email_to"]],
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_welcome_email(data: Dict):
    """
    Send welcome email after account activation.

    Args:
        data: Dictionary containing user details including:
            - email_to: Recipient's email address
            - first_name: User's first name
            - last_name: User's last name
            - email: User's email address
            - account_type: Type of account (CUSTOMER, ADMIN)
            - join_date: Date user joined
            - dashboard_url: URL to user dashboard
    """
    template = template_env.get_template("welcome_email.html")

    context = {
        "recipient_email": data["email_to"],
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "account_type": data["account_type"],
        "join_date": data["join_date"],
        "dashboard_url": data.get(
            "dashboard_url", "https://nylabank.qa.maoney.co/dashboard"
        ),
    }

    html_content = template.render(**context)

    message = MessageSchema(
        subject="Welcome to NylaBank!",
        recipients=[data["email_to"]],
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


# Legacy function for backward compatibility
async def send_email_verification_code_legacy(data: Dict):
    """
    Legacy function for backward compatibility.
    Use send_email_verification_code instead.
    """
    return await send_email_verification_code(data)
