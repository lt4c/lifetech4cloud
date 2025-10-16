"""add admin rbac tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20251002_admin_rbac"
down_revision = "20251001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "roles" not in existing_tables:
        op.create_table(
            "roles",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=64), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.UniqueConstraint("name", name="uq_roles_name"),
        )

    if "permissions" not in existing_tables:
        op.create_table(
            "permissions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("code", sa.String(length=128), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.UniqueConstraint("code", name="uq_permissions_code"),
        )

    if "user_roles" not in existing_tables:
        op.create_table(
            "user_roles",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "role_id"),
            sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
        )

    if "role_permissions" not in existing_tables:
        op.create_table(
            "role_permissions",
            sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("role_id", "permission_id"),
            sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
        )

    if "audit_logs" not in existing_tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("action", sa.String(length=128), nullable=False),
            sa.Column("target_type", sa.String(length=128), nullable=False),
            sa.Column("target_id", sa.String(length=128), nullable=True),
            sa.Column("diff_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column("ua", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    if "service_status" not in existing_tables:
        op.create_table(
            "service_status",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("service_name", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=False),
            sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.UniqueConstraint("service_name", name="uq_service_status_name"),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "service_status" in existing_tables:
        op.drop_table("service_status")
    if "audit_logs" in existing_tables:
        op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
        op.drop_table("audit_logs")
    if "role_permissions" in existing_tables:
        op.drop_table("role_permissions")
    if "user_roles" in existing_tables:
        op.drop_table("user_roles")
    if "permissions" in existing_tables:
        op.drop_table("permissions")
    if "roles" in existing_tables:
        op.drop_table("roles")
