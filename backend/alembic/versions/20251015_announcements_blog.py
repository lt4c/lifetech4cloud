"""expand announcements for rich content"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20251015_announcements_blog"
down_revision = "20251014_worker_refactor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    attachments_type = postgresql.JSONB(astext_type=sa.Text())

    op.add_column("announcements", sa.Column("slug", sa.String(length=191), nullable=True))
    op.add_column("announcements", sa.Column("excerpt", sa.Text(), nullable=True))
    op.add_column("announcements", sa.Column("content", sa.Text(), nullable=True))
    op.add_column("announcements", sa.Column("hero_image_url", sa.String(length=500), nullable=True))
    op.add_column(
        "announcements",
        sa.Column(
            "attachments",
            attachments_type,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    conn = op.get_bind()
    updates = """
        UPDATE announcements
        SET
            slug = lower(replace(id::text, '-', '')),
            excerpt = COALESCE(message, ''),
            content = COALESCE(message, '')
    """
    conn.execute(sa.text(updates))

    op.alter_column("announcements", "slug", nullable=False)
    op.alter_column("announcements", "content", nullable=False, server_default="")

    op.create_index("uq_announcements_slug", "announcements", ["slug"], unique=True)

    op.alter_column("announcements", "attachments", server_default=None)


def downgrade() -> None:
    op.alter_column("announcements", "attachments", server_default=sa.text("'[]'::jsonb"))
    op.drop_index("uq_announcements_slug", table_name="announcements")
    op.drop_column("announcements", "attachments")
    op.drop_column("announcements", "hero_image_url")
    op.drop_column("announcements", "content")
    op.drop_column("announcements", "excerpt")
    op.drop_column("announcements", "slug")

