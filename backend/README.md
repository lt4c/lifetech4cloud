# Discord Login FastAPI

This project exposes a production-ready FastAPI service that performs Discord OAuth2 login (authorization code flow) with automatic user provisioning backed by PostgreSQL. It ships with a minimal HTML test client and Docker Compose deployment for one-command startup.

## Features
- Discord OAuth2 login using the `identify` and `email` scopes via `httpx`.
- Automatic user provisioning and field updates on repeated logins (email, username, display name, avatar URL).
- Signed HttpOnly cookie session powered by `itsdangerous`; Secure and SameSite=Lax toggled via environment.
- PostgreSQL persistence with SQLAlchemy 2.x and Alembic migrations executed automatically on app startup.
- `/me` endpoint exposing the authenticated profile and `/health` endpoint verifying API and DB connectivity.
- Lightweight Jinja2 page to exercise the flow (login button, profile preview, DB health badge, logout button).
- **Rewarded ads stack**: Monetag (client ticket flow) plus Google Ad Manager / IMA (SSV) with nonce issuance, Cloudflare Turnstile bot mitigation, Redis-backed idempotency, wallet ledgering, and Prometheus metrics. The `/earn` page only lazy-loads the SDK required for the selected provider.

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

### Rewarded Ads configuration

| Variable | Purpose |
|----------|---------|
| `REWARD_AMOUNT` | Coins granted for each successful rewarded ad (default `5`) |
| `REQUIRED_DURATION` | Minimum duration in seconds reported by the ad network (default `30`) |
| `MIN_INTERVAL` | Cool-down in seconds between rewards for the same user/device (default `30`) |
| `DAILY_CAP_USER` | Hard daily cap per user before adaptive throttling (default `40`) |
| `DAILY_CAP_DEVICE` | Daily cap per device fingerprint (default `60`) |
| `RWD_PER_DAY_MIN` | Lower bound when adaptive cap reduces quota (default `20`) |
| `DEFAULT_PROVIDER` | Default ad provider key when clients omit the selection (default `monetag`) |
| `ENABLE_MONETAG` | Toggle Monetag provider availability (default `true`) |
| `MONETAG_ZONE_ID` | Monetag zone identifier rendered on the frontend |
| `MONETAG_SCRIPT_URL` | Monetag script URL loaded by the client |
| `MONETAG_TICKET_SECRET` | Secret used to sign Monetag tickets (falls back to `SECRET_KEY`) |
| `MONETAG_TICKET_TTL` | Ticket lifetime in seconds (default `180`) |
| `ENABLE_GMA` | Toggle Google Ad Manager / IMA provider (default `true`) |
| `SSV_FAIL_THRESHOLD` | Failure ratio in 30 min window that triggers adaptive cap (default `0.2`) |
| `AD_TAG_BASE` | Base GAM ad tag URL used to issue IMA requests (must include your network & line items) |
| `PRICE_FLOOR` | Optional CPM floor appended via `cust_params` |
| `SSV_SECRET` | Shared secret for HMAC SHA-256 validation (leave blank when using `PUBLIC_KEY_PATH`) |
| `PUBLIC_KEY_PATH` | Path to PEM public key for RS256 verification (take precedence over `SSV_SECRET`) |
| `CLIENT_SIGNING_SECRET` | Optional HMAC secret for FE→BE request signing (`X-Client-Signature`) |
| `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile credentials used on `/ads/prepare` |
| `TURNSTILE_MIN_SCORE` | Minimum Turnstile score (default `0.5`) |
| `TURNSTILE_ALLOW_MISSING` | Set `true` để bỏ qua Turnstile trong môi trường dev |
| `ADS_BLOCKED_ASN` | CSV list of ASNs to reject (VPN/hosts) |
| `ADS_BLOCKED_IPS` | CIDR ranges to block at prepare time |
| `ADS_ALLOWED_PLACEMENTS` | Comma list of placement names embedded into `cust_params` (default `earn,daily,boost,test`) |
| `REDIS_URL` | Redis connection string for nonce store, rate limiting and adaptive cap (`redis://redis:6379/0`) |

Frontend `.env` values:

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | API origin used by the Vite build |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key dùng cho `/earn` |
| `VITE_ADS_CLIENT_SIGNING_KEY` | Mirrors `CLIENT_SIGNING_SECRET` when FE signing is enabled |

## Rewarded Ads Flow

1. **Prepare (`POST /ads/prepare`)** ? The browser requests a session with placement, client hints, and Turnstile token. The backend enforces ASN/IP policy, cooldown, quotas, and issues either a Monetag ticket bundle or a GAM ad tag together with the hashed `deviceHash`. Monetag is returned by default unless the client explicitly selects Google.
2. **Monetag completion (`POST /ads/complete`)** ? The frontend loads the Monetag script, verifies the tab stays visible for `REQUIRED_DURATION`, then sends `{nonce, ticket, durationSec, deviceHash}`. The backend validates the HMAC ticket, acquires a Redis/in-memory nonce lock, checks quotas again, and credits the wallet.
3. **Google IMA SSV (`/ads/ssv`)** ? When the provider is `gma`, the page plays the returned ad tag via the Google IMA SDK. Google calls back with an SSV payload signed with HMAC/RS256; the backend validates signature, cooldown, quotas, and idempotency before rewarding.
4. **Wallet refresh** ? After a reward, the frontend refreshes `/wallet` and the authenticated profile. Every grant persists an `ad_rewards` record plus a matching wallet ledger entry.

### Anti-fraud measures
- Device fingerprint derived from UA, Client Hints, and IP subnet.
- Redis-backed nonce storage (`ads:nonce:*`) and event idempotency (`ads:event:*`).
- Adaptive cap reduces `DAILY_CAP_USER` when `SSV_FAIL_THRESHOLD` is breached in the last 30 minutes.
- Optional `X-Client-Signature` header (`HMAC(userId|clientNonce|timestamp|placement)`).
- `RateLimiter` now uses Redis for distributed throttling (`20 req / 2s` on `/ads/prepare`, `5 req / 10s` on `/ads/ssv`).
- Metrics exported at `/metrics`: success/error counters, reward totals, failure ratio, effective cap.

Grafana dashboards can scrape the Prometheus exposition directly. Example useful series:

| Metric | Description |
|--------|-------------|
| `rewarded_ads_prepare_total{status="ok"}` | Successful `/ads/prepare` responses |
| `rewarded_ads_ssv_total{status="success"}` | Verified SSV callbacks |
| `rewarded_ads_reward_amount_total` | Total coins granted (labelled by `network` / `placement`) |
| `rewarded_ads_failure_ratio` | Rolling failure ratio used for adaptive cap |
| `rewarded_ads_effective_daily_cap` | Current dynamic per-user quota |

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
