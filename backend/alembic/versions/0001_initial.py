"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scan_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("normalized_url", sa.String(2048), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "completed", "failed", name="scanstatus"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column(
            "risk_level",
            sa.Enum("green", "yellow", "red", name="risklevel"),
            nullable=True,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "scan_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scan_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_html_snapshot", sa.Text(), nullable=True),
        sa.Column("pages_checked", postgresql.JSONB(), nullable=True),
        sa.Column("checks", postgresql.JSONB(), nullable=True),
        sa.Column("issues", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"])
    op.create_index("ix_scan_jobs_created_at", "scan_jobs", ["created_at"])
    op.create_index("ix_scan_results_scan_id", "scan_results", ["scan_id"])


def downgrade() -> None:
    op.drop_index("ix_scan_results_scan_id", "scan_results")
    op.drop_index("ix_scan_jobs_created_at", "scan_jobs")
    op.drop_index("ix_scan_jobs_status", "scan_jobs")
    op.drop_table("scan_results")
    op.drop_table("scan_jobs")
    op.execute("DROP TYPE IF EXISTS scanstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")
