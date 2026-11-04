"""Link application profiles to Supabase Auth users.

Revision ID: 0002_supabase_auth_users
Revises: 0001_initial
Create Date: 2026-11-04
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_supabase_auth_users"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("auth_user_id", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_users_auth_user_id",
        "users",
        ["auth_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_auth_user_id", table_name="users")
    op.drop_column("users", "auth_user_id")

