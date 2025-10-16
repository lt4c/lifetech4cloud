# Mapping

## User Model ? Admin DTO

| ORM Column | Admin DTO Field | Notes |
|------------|-----------------|-------|
| `users.id` | `AdminUser.id` | UUID preserved |
| `users.discord_id` | `AdminUser.discord_id` | Exposed for reference only |
| `users.username` | `AdminUser.username` | Editable via admin API |
| `users.email` | `AdminUser.email` | Optional; retains existing value |
| `users.display_name` | `AdminUser.display_name` | Nullable field |
| `users.avatar_url` | `AdminUser.avatar_url` | Used for profile rendering |
| `users.phone_number` | `AdminUser.phone_number` | Always nullable (Discord does not supply) |
| `users.created_at` | — | Available in ORM responses; not included in DTO to avoid schema changes |
| `users.updated_at` | — | Same as above |

## Auth Dependencies ? Admin Guard

| Existing Component | Admin Equivalent | Description |
|--------------------|------------------|-------------|
| `get_current_user` (cookie session) | `require_perm("code")` | Wraps the existing dependency, resolves permissions, enforces rate limiting and CSRF before returning the `User` instance. |
| Session cookie (`SESSION_COOKIE_NAME`) | CSRF token | CSRF token derives from the signed session cookie and request path. |

## Error Contract

Existing FastAPI routes return the default `{"detail": "message"}` shape. Admin APIs preserve this contract for all authorization, validation, and conflict errors so downstream clients receive a consistent payload.
