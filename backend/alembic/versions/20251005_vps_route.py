"""placeholder migration for transitional VPS route changes.

The actual worker route column is created in revision `20251014_worker_refactor`.
This revision exists only to maintain a linear migration history after older
drafts were replaced.
"""

from __future__ import annotations

revision = "20251005_vps_route"
down_revision = "20251005_worker_system"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op placeholder."""
    pass


def downgrade() -> None:
    """No-op placeholder."""
    pass

