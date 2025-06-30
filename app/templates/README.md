# Email Templates

This directory contains beautiful, responsive email templates for NylaBank using Tailwind CSS and Jinja2 templating.

## Template Structure

### Base Template (`base.html`)

The foundation template that provides:

- **Responsive Design**: Works on all devices and email clients
- **Tailwind CSS**: Modern styling with custom color palette
- **Branding**: NylaBank logo and consistent styling
- **Modular Blocks**: Easy to extend and customize
- **Email Compatibility**: Optimized for email clients

### Available Templates

#### 1. Registration Verification (`registration_verification.html`)

- **Purpose**: Email verification for new account registration
- **Variables**: `verify_code`
- **Features**:
  - Clear verification code display
  - Security information
  - Expiration notice

#### 2. Password Reset (`password_reset.html`)

- **Purpose**: Password reset verification
- **Variables**: `reset_code`
- **Features**:
  - Security-focused design
  - Warning notices
  - Clear instructions

#### 3. Transaction Notification (`transaction_notification.html`)

- **Purpose**: Transaction completion notifications
- **Variables**:
  - `transaction_type`, `reference_number`, `amount`, `currency`
  - `account_number`, `balance_after`, `transaction_date`
  - `description`, `from_account_last4`, `to_account_last4`
  - `dashboard_url`
- **Features**:
  - Detailed transaction information
  - Account balance tracking
  - Transfer-specific details
  - Action buttons

#### 4. Welcome Email (`welcome_email.html`)

- **Purpose**: Welcome new users after account activation
- **Variables**:
  - `first_name`, `last_name`, `email`
  - `account_type`, `join_date`, `dashboard_url`
- **Features**:
  - Account information display
  - Feature highlights
  - Getting started guide

## Template Blocks

The base template provides these customizable blocks:

### Content Blocks

- `title`: Page title
- `email_type`: Email category (shown in header)
- `greeting`: Main greeting text
- `subtitle`: Subtitle text
- `content`: Main email content
- `action_section`: Call-to-action buttons
- `footer_text`: Custom footer text

### Styling Features

- **Color System**: Primary, success, warning, danger color schemes
- **Icons**: SVG icons for visual appeal
- **Responsive**: Mobile-friendly design
- **Email-Safe**: Compatible with major email clients

## Usage Examples

### Using in Python Code

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Setup Jinja2 environment
template_dir = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(template_dir))

# Render registration verification email
template = env.get_template("registration_verification.html")
html_content = template.render(
    verify_code="123456",
    recipient_email="user@example.com"
)
```

### Using with FastAPI Mail

```python
from fastapi_mail import FastMail, MessageSchema
from app.templates import render_email_template

# Render template
html_content = render_email_template(
    "registration_verification.html",
    verify_code="123456",
    recipient_email="user@example.com"
)

# Send email
message = MessageSchema(
    subject="Verify Your Email - NylaBank",
    recipients=["user@example.com"],
    body=html_content,
    subtype="html"
)
await fastmail.send_message(message)
```

## Customization

### Adding New Templates

1. Create a new `.html` file
2. Extend the base template: `{% extends "base.html" %}`
3. Override the necessary blocks
4. Add your custom content

### Modifying Colors

Update the Tailwind config in `base.html`:

```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        primary: {
          // Your custom colors
        },
      },
    },
  },
};
```

### Adding New Variables

1. Update the template to use new variables
2. Pass variables when rendering
3. Document in this README

## Best Practices

1. **Keep it Simple**: Email clients have limited CSS support
2. **Test Thoroughly**: Test in multiple email clients
3. **Use Inline Styles**: Some email clients strip `<style>` tags
4. **Mobile First**: Design for mobile devices first
5. **Accessibility**: Use proper contrast and readable fonts
6. **Brand Consistency**: Maintain NylaBank branding

## Email Client Compatibility

- ✅ Gmail (Web & Mobile)
- ✅ Outlook (Desktop & Web)
- ✅ Apple Mail
- ✅ Yahoo Mail
- ✅ Thunderbird
- ✅ Mobile email apps

## Support

For questions about email templates or customization, contact the development team.
