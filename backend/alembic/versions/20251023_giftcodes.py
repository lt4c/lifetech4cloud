"""add gift code redemption tables

Revision ID: 20251023_giftcodes
Revises: 20251020_rewarded_ads
Create Date: 2025-10-23 21:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251023_giftcodes"
down_revision = "20251020_rewarded_ads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gift_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("reward_amount", sa.Integer(), nullable=False),
        sa.Column("total_uses", sa.Integer(), nullable=False),
        sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_gift_codes_code", "gift_codes", ["code"])

    op.create_table(
        "gift_code_redemptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("gift_code_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gift_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reward_amount", sa.Integer(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_gift_code_redemptions_user", "gift_code_redemptions", ["gift_code_id", "user_id"])
    op.create_index("ix_gift_code_redemptions_gift_code_id", "gift_code_redemptions", ["gift_code_id"])
    op.create_index("ix_gift_code_redemptions_user_id", "gift_code_redemptions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_gift_code_redemptions_user_id", table_name="gift_code_redemptions")
    op.drop_index("ix_gift_code_redemptions_gift_code_id", table_name="gift_code_redemptions")
    op.drop_constraint("uq_gift_code_redemptions_user", "gift_code_redemptions", type_="unique")
    op.drop_table("gift_code_redemptions")

    op.drop_constraint("uq_gift_codes_code", "gift_codes", type_="unique")
    op.drop_table("gift_codes")
