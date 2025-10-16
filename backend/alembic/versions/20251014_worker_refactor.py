"""refactor worker infrastructure and product associations"""

from alembic import op
import sqlalchemy as sa


revision = "20251014_worker_refactor"
down_revision = "20251012_announcements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # workers adjustments
    with op.batch_alter_table("workers") as batch:
        batch.add_column(sa.Column("max_sessions", sa.Integer(), nullable=False, server_default="3"))
        batch.add_column(
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))
        )
        batch.drop_constraint("ck_workers_status", type_="check")
        batch.create_check_constraint("ck_workers_status", "status in ('active','disabled')")
        batch.drop_column("last_net_mbps")
        batch.drop_column("last_req_rate")
        batch.drop_column("current_jobs")
        batch.drop_column("last_heartbeat")
        batch.drop_column("token_id")

    op.execute(sa.text("DROP INDEX IF EXISTS ix_workers_last_heartbeat"))

    # vps products
    op.add_column(
        "vps_products",
        sa.Column("provision_action", sa.Integer(), nullable=False, server_default="1"),
    )

    # vps sessions
    op.add_column(
        "vps_sessions",
        sa.Column("worker_route", sa.String(length=128), nullable=True),
    )

    # association table
    op.create_table(
        "vps_product_workers",
        sa.Column(
            "product_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vps_products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "worker_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # drop server defaults where unsuitable
    op.alter_column("workers", "max_sessions", server_default=None)
    op.alter_column("workers", "updated_at", server_default=None)
    op.alter_column("vps_products", "provision_action", server_default=None)


def downgrade() -> None:
    op.alter_column("vps_products", "provision_action", server_default="1")
    op.drop_table("vps_product_workers")

    op.drop_column("vps_sessions", "worker_route")
    op.drop_column("vps_products", "provision_action")

    with op.batch_alter_table("workers") as batch:
        batch.add_column(sa.Column("token_id", sa.UUID(as_uuid=True), nullable=True))
        batch.add_column(sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("current_jobs", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("last_req_rate", sa.Numeric(), nullable=True))
        batch.add_column(sa.Column("last_net_mbps", sa.Numeric(), nullable=True))
        batch.drop_column("updated_at")
        batch.drop_column("max_sessions")
        batch.drop_constraint("ck_workers_status", type_="check")
        batch.create_check_constraint(
            "ck_workers_status",
            "status in ('idle','busy','offline')",
        )

    op.create_index("ix_workers_last_heartbeat", "workers", ["last_heartbeat"])
