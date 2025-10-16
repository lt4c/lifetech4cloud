"""placeholder migration for legacy worker system configuration.

This revision intentionally performs no schema changes. The worker system
changes introduced during this date were superseded by the consolidated
refactor in `20251014_worker_refactor`.
"""

from __future__ import annotations

revision = "20251005_worker_system"
down_revision = "20251004_vps_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op placeholder."""
    pass


def downgrade() -> None:
    """No-op placeholder."""
    pass

