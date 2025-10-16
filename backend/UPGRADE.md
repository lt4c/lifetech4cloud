# Upgrade Guide

1. Set `ADMIN_ENABLED=true` in your environment or `.env` file to activate the admin package.
2. Run Alembic migrations to add RBAC tables:
   ```bash
   alembic upgrade head
   ```
3. (Optional) Define `ADMIN_DEFAULT_PASSWORD` to enable the bootstrap flow for granting the first admin role. After claiming, remove or rotate the secret.
4. Visit `/admin/status` (or the configured `ADMIN_PREFIX`) to verify API health, dependency checks, and database diagnostics.
