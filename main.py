from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.users import user_router
from app.api.v1.accounts import account_router
from app.api.v1.transactions import transaction_router
from app.api.v1.admin import admin_router

from scalar_fastapi import get_scalar_api_reference
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

description = """
NylaBank API is a modern, secure digital banking platform for managing users, accounts, and transactions.

### Key Features

- **User Management**
  - Register, verify, and authenticate users
  - Role-based access (Customer, Admin)
  - Profile management and password reset via email OTP

- **Account Management**
  - Create, view, and delete bank accounts (Checking, Savings, etc.)
  - Automated account number generation
  - Real-time balance tracking and account statements

- **Transactions**
  - Deposit, withdraw, and transfer funds between accounts
  - Transaction history with pagination and filtering
  - Automatic reference number generation for each transaction
  - Email notifications for all major account activities

- **Admin & Analytics**
  - Admin endpoints for user and account oversight
  - Daily summaries and advanced reporting
  - Secure access to sensitive operations

- **Security & Compliance**
  - JWT-based authentication
  - CORS and environment-based configuration
  - Email verification and OTP for sensitive actions

- **Developer Experience**
  - Fully async FastAPI backend
  - Modular, versioned API structure (`/api/v1/`)
  - Interactive API docs (Swagger, Redoc, Scalar)
  - Comprehensive test suite and CI/CD integration

---

**Typical Workflow:**
1. User registers and verifies email via OTP.
2. User creates one or more bank accounts.
3. User performs deposits, withdrawals, and transfers.
4. All actions are logged, and notifications are sent via email.
5. Admins can monitor, audit, and manage all users and accounts.

---

For more details, see the documentation below or contact support.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="NyLabank API",
    description=description,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
        show_sidebar=True,
        hide_download_button=True,
        hide_models=True,
        dark_mode=True,
        # hidden_clients=["python", "go"],
        servers=[
            {"url": "https://nylabankapi.prod.maoney.co"},
            {"url": "http://localhost:8000"},
            {"url": "http://127.0.0.1:8000"},
        ],
        default_open_all_tags=True,
        scalar_theme="",  # "alternate, default, moon, purple, solarized, bluePlanet, saturn, kepler, mars, deepSpace, none"
    )

    # # Inject the custom CSS file into the HTML
    # custom_css = '<link rel="stylesheet" href="/static/super_dark.css">'
    # modified_html_content = scalar_html_content.replace(
    #     "<head>",
    #     f"<head>{custom_css}"
    # )
    # return HTMLResponse(content=modified_html_content)


app.include_router(
    user_router.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"],
)

app.include_router(
    account_router.router,
    prefix=f"{settings.API_V1_STR}/accounts",
    tags=["accounts"],
)

app.include_router(
    transaction_router.router,
    prefix=f"{settings.API_V1_STR}/transactions",
    tags=["transactions"],
)

app.include_router(
    admin_router.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["admin"],
)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page():
    return """
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>NyLabank API Landing Page</title>
        <style>
            body {
                background: #181c20;
                color: #f3f3f3;
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: #23272b;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.3);
                padding: 2.5rem 2rem 2rem 2rem;
                max-width: 420px;
                width: 90vw;
                margin: 2rem auto;
                text-align: center;
            }
            h1 {
                margin-bottom: 0.5rem;
                font-size: 2.2rem;
                color: #4a90e2;
            }
            p {
                color: #b0b8c1;
                margin-bottom: 2rem;
            }
            .links {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            a {
                background: #4a90e2;
                color: #ffffff;
                text-decoration: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-weight: 600;
                font-size: 1.1rem;
                transition: background 0.2s, color 0.2s, box-shadow 0.2s;
                box-shadow: 0 2px 8px rgba(74,144,226,0.08);
            }
            a:hover {
                background: #5ba0f2;
                color: #ffffff;
                box-shadow: 0 4px 16px rgba(74,144,226,0.18);
            }
            .footer {
                margin-top: 2rem;
                color: #6c757d;
                font-size: 0.95rem;
            }
        </style>
    </head>
    <body>
        <div class=\"container\">
            <h1>NyLabank API</h1>
            <p>Welcome to the NyLabank API. Choose a documentation below:</p>
            <div class=\"links\">
                <a href=\"/docs\">Swagger UI</a>
                <a href=\"/redoc\">Redoc</a>
                <a href=\"/scalar\">Scalar Docs</a>
            </div>
            <div class=\"footer\">&copy; 2024 NyLabank. All rights reserved.</div>
        </div>
    </body>
    </html>
    """
