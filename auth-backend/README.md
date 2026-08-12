# auth-backend

FastAPI authentication service providing JWT-based login, registration, password reset, and token refresh.

---

## Overview

This service exposes a REST API under `/auth` and is the authoritative backend for the auth-starter project. It uses:

- **FastAPI** — ASGI web framework
- **SQLAlchemy** — ORM (async-compatible)
- **psycopg** — PostgreSQL driver
- **python-jose** — JWT encoding/decoding
- **passlib[bcrypt]** — password hashing
- **uvicorn** — ASGI server

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Authenticate and receive tokens |
| GET | `/auth/me` | Return the authenticated user's profile |
| POST | `/auth/logout` | Revoke the current refresh token |
| POST | `/auth/refresh` | Rotate and issue a new access + refresh token pair |
| POST | `/auth/forgot-password` | Send a password-reset email |
| POST | `/auth/reset-password` | Apply a new password using a reset token |

---

## Project structure

```
auth-backend/
├── app/
│   ├── main.py            # FastAPI application factory
│   ├── config.py          # Settings (reads from environment)
│   ├── database.py        # SQLAlchemy engine + session
│   ├── auth/
│   │   ├── router.py      # Route handlers
│   │   ├── service.py     # Business logic
│   │   └── schemas.py     # Pydantic request/response models
│   └── models/
│       ├── user.py
│       ├── password_reset.py
│       └── refresh_token.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Requirements

- Python 3.12+
- PostgreSQL 15+

---

## Local setup

### 1. Clone and enter the directory

```bash
git clone <repo-url>
cd auth-backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

See the [Environment variables](#environment-variables) section below for descriptions of every key.

### 5. Apply database schema

Run the SQL schema against your PostgreSQL instance:

```bash
psql "$DATABASE_URL" -f ../schema.sql
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Docker

### Build the image

```bash
docker build -t auth-backend .
```

### Run the container

```bash
docker run --env-file .env -p 8000:8000 auth-backend
```

Or use the project-level `docker-compose.yml` from the repository root:

```bash
docker compose up --build
```

---

## Running tests

```bash
pytest
```

Tests cover: register → login → refresh → forgot-password → reset-password → logout, plus negative cases (duplicate email, weak password, password mismatch, expired token).

---

## Environment variables

### Database

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | SQLAlchemy connection string for PostgreSQL via psycopg | `postgresql+psycopg://user:password@localhost:5432/auth_db` |

### JWT

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key used to sign access tokens. Must be long and random. | `change-me-to-a-long-random-secret` |
| `JWT_ALGORITHM` | Signing algorithm for JWTs | `HS256` |
| `JWT_ACCESS_TOKEN_TTL_MINUTES` | Lifetime of an access token in minutes | `15` |

### Bcrypt

| Variable | Description | Example |
|----------|-------------|---------|
| `BCRYPT_ROUNDS` | Work factor for bcrypt password hashing (minimum 12) | `12` |

### Password reset

| Variable | Description | Example |
|----------|-------------|---------|
| `RESET_TOKEN_TTL_MINUTES` | Lifetime of a password-reset token in minutes | `60` |

### Refresh tokens

| Variable | Description | Example |
|----------|-------------|---------|
| `REFRESH_TOKEN_TTL_DAYS` | Lifetime of a standard refresh token in days | `7` |
| `REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS` | Lifetime of a refresh token when "remember me" is selected | `30` |

### SMTP (password reset emails)

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | Hostname of the SMTP server | `smtp.example.com` |
| `SMTP_PORT` | Port for the SMTP connection | `587` |
| `SMTP_USERNAME` | SMTP authentication username | `no-reply@example.com` |
| `SMTP_PASSWORD` | SMTP authentication password | `smtp-password` |
| `SMTP_FROM_ADDRESS` | Email address used in the `From` header | `no-reply@example.com` |
| `SMTP_FROM_NAME` | Display name used in the `From` header | `Auth Starter` |
| `SMTP_TLS` | Whether to use STARTTLS (`true` or `false`) | `true` |

### Rate limiting

| Variable | Description | Example |
|----------|-------------|---------|
| `RATE_LIMIT_LOGIN_MAX_ATTEMPTS` | Maximum login attempts allowed per window | `5` |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS` | Duration of the login rate-limit window in seconds | `60` |
| `RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS` | Maximum forgot-password requests allowed per window | `3` |
| `RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS` | Duration of the forgot-password rate-limit window in seconds | `300` |

### Application

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_BASE_URL` | Public base URL of the frontend application (used in reset-password links) | `http://localhost:3000` |
| `CORS_ORIGIN` | Allowed CORS origin for the frontend | `http://localhost:3000` |

---

## Security notes

- Passwords are hashed with bcrypt at the configured `BCRYPT_ROUNDS` (≥ 12). Plaintext passwords are never stored or logged.
- Password-reset and refresh tokens are stored as SHA-256 hashes; the raw token is only ever transmitted once over the wire.
- Login failures always return "Invalid email or password." regardless of whether the email exists (enumeration resistance).
- Forgot-password always returns the same generic response regardless of whether the supplied email is registered.
- Refresh tokens rotate on every use and are fully revoked on logout.
