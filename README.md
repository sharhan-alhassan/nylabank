# NylaBank API

A modern, secure banking API for user accounts, transactions, and admin operations.

---

## 🚀 CI/CD

- Automated with GitHub Actions and Kubernetes (see `k8s_deploy/`)
- Push to `main` triggers build, test, and deploy

## 📚 API Documentation

- Interactive docs: `/docs` (Swagger UI)

![User Registration](images/swagger.png)

- Redoc: `/redoc`

![Redoc ](images/redoc.png)

- Scalar: `/scalar`

![Interractive Docs & API Client](images/api_docs_scalar.png)

- Versioned: `/api/v1/`

## 👤 User Creation Flow

1. Register with email & password
2. Receive verification email
3. Verify code to activate account
4. Login and create bank accounts

![User Registration](images/email_register.png)

## 💳 Accounts & Transactions

- **Accounts**: Create, list, delete, get statements
- **Transactions**: Deposit, withdraw, transfer, view history

![Welcome Notification](images/welcome_flash.png)

![Welcome Notification](images/welcome_detail.png)

## Password Reset
![Password Reset](images/password_reset_flash.png)

![Password Reset](images/password_reset_detail.png)

## 🗄️ Database Schemas

- Users, Accounts, Transactions, OTPs
- Enum types for roles, account types, transaction types

![Account DB Schema](images/db_accounts.png)

### Transaction Demo

- Deposit/Withdraw: Instant balance update
- Transfer: Between user accounts

![Transaction Notification](images/transaction.png)

## 🏗️ Architecture

- FastAPI backend
- PostgreSQL (async)
- Alembic migrations
- Modular routers: users, accounts, transactions, admin
- Email notifications (Jinja2 templates)

---

## 🛠️ Local Development

```sh
# Migrate DB
alembic upgrade head
# Start server
uvicorn main:app --reload --port 8000
```

---

## Seed Data
- 
## 📬 Contact & Support

- Email: sharhanalhassan@gmail.com

---

> See code for more details!
