"""add vps platform and support tables"""

from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20251004_vps_platform"
down_revision = "20251002_admin_rbac"
branch_labels = None
depends_on = None


def _table_exists(inspector, name: str) -> bool:
    return name in set(inspector.get_table_names())


def _column_exists(inspector, table: str, column: str) -> bool:
    try:
        columns = inspector.get_columns(table)
    except Exception:  # pragma: no cover - table might not exist
        return False
    return any(col["name"] == column for col in columns)



def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _column_exists(inspector, "users", "coins"):
        op.add_column(
            "users",
            sa.Column("coins", sa.Integer(), nullable=False, server_default="0"),
        )
        op.execute(sa.text("UPDATE users SET coins = 0 WHERE coins IS NULL"))
        op.alter_column("users", "coins", server_default="0")

    if not _table_exists(inspector, "admin_tokens"):
        op.create_table(
            "admin_tokens",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("label", sa.String(length=128), nullable=False),
            sa.Column("token_ciphertext", sa.Text(), nullable=False),
            sa.Column("token_prefix", sa.String(length=4), nullable=False),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        )

    if not _table_exists(inspector, "workers"):
        op.create_table(
            "workers",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=128), nullable=True),
            sa.Column("base_url", sa.Text(), nullable=False),
            sa.Column("token_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="idle"),
            sa.Column("current_jobs", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_net_mbps", sa.Numeric(), nullable=True),
            sa.Column("last_req_rate", sa.Numeric(), nullable=True),
            sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["token_id"], ["admin_tokens.id"], ondelete="SET NULL"),
            sa.CheckConstraint(
                "status in ('idle','busy','offline')",
                name="ck_workers_status",
            ),
        )
        op.create_index("ix_workers_last_heartbeat", "workers", ["last_heartbeat"])

    if not _table_exists(inspector, "vps_products"):
        op.create_table(
            "vps_products",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price_coins", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    if not _table_exists(inspector, "vps_sessions"):
        op.create_table(
            "vps_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("worker_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("session_token", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column(
                "checklist",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column("rdp_host", sa.String(length=255), nullable=True),
            sa.Column("rdp_port", sa.Integer(), nullable=True),
            sa.Column("rdp_user", sa.String(length=128), nullable=True),
            sa.Column("rdp_password", sa.String(length=128), nullable=True),
            sa.Column("log_url", sa.Text(), nullable=True),
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["product_id"], ["vps_products.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["worker_id"], ["workers.id"], ondelete="SET NULL"),
            sa.CheckConstraint(
                "status in ('pending','provisioning','ready','failed','expired','deleted')",
                name="ck_vps_sessions_status",
            ),
        )
        op.create_index("ix_vps_sessions_user_id", "vps_sessions", ["user_id"])
        op.create_index("ix_vps_sessions_product_id", "vps_sessions", ["product_id"])
        op.create_index("ix_vps_sessions_worker_id", "vps_sessions", ["worker_id"])
        op.create_index("ix_vps_sessions_created_at", "vps_sessions", ["created_at"])
        op.create_index("ix_vps_sessions_idempotency_key", "vps_sessions", ["idempotency_key"])


    if not _table_exists(inspector, "ads_claims"):
        op.create_table(
            "ads_claims",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("nonce", sa.String(length=128), nullable=False),
            sa.Column("value_coins", sa.Integer(), nullable=False),
            sa.Column("claimed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.CheckConstraint("provider in ('adsense','monetag')", name="ck_ads_claims_provider"),
            sa.UniqueConstraint("nonce", name="uq_ads_claims_nonce"),
        )
        op.create_index("ix_ads_claims_user_id", "ads_claims", ["user_id"])
        op.create_index("ix_ads_claims_claimed_at", "ads_claims", ["claimed_at"])
    if not _table_exists(inspector, "support_threads"):
        op.create_table(
            "support_threads",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("source", sa.String(length=16), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.CheckConstraint("source in ('ai','human')", name="ck_support_threads_source"),
            sa.CheckConstraint(
                "status in ('open','pending','resolved','closed')",
                name="ck_support_threads_status",
            ),
        )
        op.create_index("ix_support_threads_user_id", "support_threads", ["user_id"])

    if not _table_exists(inspector, "support_messages"):
        op.create_table(
            "support_messages",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("sender", sa.String(length=16), nullable=False),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("role", sa.String(length=32), nullable=True),
            sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["thread_id"], ["support_threads.id"], ondelete="CASCADE"),
            sa.CheckConstraint(
                "sender in ('user','ai','admin')",
                name="ck_support_messages_sender",
            ),
        )
        op.create_index("ix_support_messages_thread_id", "support_messages", ["thread_id"])

    if not _table_exists(inspector, "settings"):
        op.create_table(
            "settings",
            sa.Column("key", sa.String(length=191), primary_key=True, nullable=False),
            sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    defaults = [
        ("ads.enabled", {"enabled": False}),
        (
            "kyaro.system_prompt",
            {
                "prompt": "Bạn là Kyaro, trợ lý hỗ trợ người dùng...",
            },
        ),
    ]

    conn = op.get_bind()
    stmt = sa.text(
        "INSERT INTO settings (key, value) VALUES (:key, CAST(:value AS jsonb)) ON CONFLICT (key) DO NOTHING"
    )
    for key, value in defaults:
        conn.execute(stmt, {"key": key, "value": json.dumps(value)})



def downgrade() -> None:
    inspector = inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "support_messages" in existing_tables:
        op.drop_index("ix_support_messages_thread_id", table_name="support_messages")
        op.drop_table("support_messages")
    if "support_threads" in existing_tables:
        op.drop_index("ix_support_threads_user_id", table_name="support_threads")
        op.drop_table("support_threads")
    if "vps_sessions" in existing_tables:
        op.drop_index("ix_vps_sessions_created_at", table_name="vps_sessions")
        op.drop_index("ix_vps_sessions_worker_id", table_name="vps_sessions")
        op.drop_index("ix_vps_sessions_product_id", table_name="vps_sessions")
        op.drop_index("ix_vps_sessions_user_id", table_name="vps_sessions")
        op.drop_index("ix_vps_sessions_idempotency_key", table_name="vps_sessions")
        op.drop_table("vps_sessions")
    if "vps_products" in existing_tables:
        op.drop_table("vps_products")
    if "workers" in existing_tables:
        op.drop_index("ix_workers_last_heartbeat", table_name="workers")
        op.drop_table("workers")
    if "admin_tokens" in existing_tables:
        op.drop_table("admin_tokens")
    if "settings" in existing_tables:
        op.drop_table("settings")
    if "ads_claims" in existing_tables:
        op.drop_index("ix_ads_claims_claimed_at", table_name="ads_claims")
        op.drop_index("ix_ads_claims_user_id", table_name="ads_claims")
        op.drop_table("ads_claims")

    if _column_exists(inspector, "users", "coins"):
        op.drop_column("users", "coins")


