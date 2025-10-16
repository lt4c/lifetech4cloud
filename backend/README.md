# Discord Login FastAPI

This project exposes a production-ready FastAPI service that performs Discord OAuth2 login (authorization code flow) with automatic user provisioning backed by PostgreSQL. It ships with a minimal HTML test client and Docker Compose deployment for one-command startup.

## Features
- Discord OAuth2 login using the `identify` and `email` scopes via `httpx`.
- Automatic user provisioning and field updates on repeated logins (email, username, display name, avatar URL).
- Signed HttpOnly cookie session powered by `itsdangerous`; Secure and SameSite=Lax toggled via environment.
- PostgreSQL persistence with SQLAlchemy 2.x and Alembic migrations executed automatically on app startup.
- `/me` endpoint exposing the authenticated profile and `/health` endpoint verifying API and DB connectivity.
- Lightweight Jinja2 page to exercise the flow (login button, profile preview, DB health badge, logout button).

## Quick Start
1. Clone the repository and copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Populate `.env` with your Discord application credentials and desired configuration values.
3. Ensure your Discord application redirect URI is set to `${BASE_URL}/auth/discord/callback` (see Discord setup below).
4. Build and start the stack:
   ```bash
   docker compose up --build
   ```
5. Visit `http://localhost:8000` and use the **Login with Discord** button. After consenting, the page will display your profile information as stored in the database.

The PostgreSQL container stores data in the `postgres_data` volume, so user records survive container restarts.

## Environment Variables
| Variable | Description |
|----------|-------------|
| `DISCORD_CLIENT_ID` | Discord application client ID |
| `DISCORD_CLIENT_SECRET` | Discord application client secret |
| `DISCORD_REDIRECT_URI` | Callback URL configured in Discord (e.g. `http://localhost:8000/auth/discord/callback`) |
| `SECRET_KEY` | Secret used to sign session and state cookies |
| `DATABASE_URL` | SQLAlchemy database URL (defaults to `postgresql+psycopg://postgres:postgres@db:5432/app`) |
| `BASE_URL` | Public base URL for the FastAPI service |
| `ALLOWED_ORIGINS` | Optional CSV list of allowed CORS origins or `*` |
| `COOKIE_SECURE` | `true` to mark cookies as Secure (enable in production with HTTPS) |
| `SESSION_COOKIE_NAME` | Name of the session cookie (default `session`) |

> **Note:** Discord's OAuth API does **not** provide phone numbers. The `phone_number` field is always stored and returned as `null`, and the HTML test page labels it accordingly.

## Discord Application Setup
1. Log into the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create (or select) an application, then add an OAuth2 redirect under **OAuth2 → General → Redirects** matching your `DISCORD_REDIRECT_URI` value.
3. Under **OAuth2 → URL Generator**, select the `identify` and `email` scopes (no bot scope required).
4. Copy the **Client ID** and **Client Secret** into your `.env` file.

## Development
- Run `uvicorn app.main:app --reload` for local development (ensure Postgres is running and `.env` configured).
- Formatting and linting:
  ```bash
  black .
  ruff check .
  ```
- Type checking:
  ```bash
  mypy .
  ```

## Deployment Notes
- The Docker image is multi-stage, ensuring a slim runtime image with dependencies baked in.
- Alembic migrations run automatically on startup via the FastAPI `startup` event.
- The session cookie is HttpOnly, SameSite=Lax, and optionally Secure. Toggle `COOKIE_SECURE=true` when serving over HTTPS.

## API Surface
- `GET /` – HTML test interface.
- `GET /health` – API/DB health payload.
- `GET /auth/discord/login` – Starts the OAuth2 flow.
- `GET /auth/discord/callback` – Handles the OAuth2 callback and issues the session cookie.
- `GET /me` – Returns the authenticated user profile (requires session cookie).
- `POST /logout` – Clears the session cookie.
## VPS Platform Extensions
- Coin-based VPS marketplace with admin-configurable products, worker registry, and session lifecycle management.
- SSE checklist streaming and worker callback security (HMAC + timestamp guard) replace raw log polling.
- Ads reward flow with nonce-based claims and provider adapters (Adsense, Monetag) guarded by feature flags.
- Support inbox with Kyaro AI assistant and human escalation paths; admin prompt editing and auditing included.
- Standalone worker service (`worker_service/`) that self-registers, receives jobs, and streams progress back to the core backend.

## Running the Worker Service
```bash
python -m worker_service  # listens on 0.0.0.0:8476
```
Provide the backend URL, admin token (plain), token id, and public worker base URL via `POST /register`. The worker signs all callbacks with the supplied token and reuses the core checklist template when reporting progress.
### Worker Deployment (Docker)

A standalone worker container is provided under `worker_service/`. Build and run it against an existing backend:

```bash
docker build -t vps-worker -f worker_service/Dockerfile .
docker run --rm -p 8476:8476 \
  -e WORKER_BACKEND_URL=https://api.example.com \
  -e WORKER_BASE_URL=https://worker-1.example.com:8476 \
  -e WORKER_ADMIN_TOKEN=plain-token-from-vault \
  -e WORKER_TOKEN_ID=token-uuid \
  -e WORKER_NAME=worker-1 \
  vps-worker
```

For local orchestration, `docker-compose.worker.yml` spins up backend + database + worker in one command.
