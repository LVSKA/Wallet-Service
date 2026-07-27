"""create wallets table

Revision ID: 0001
Revises:
Create Date: 2026-07-27 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "wallets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "balance",
            sa.Numeric(20, 0),
            nullable=False,
            server_default="0",
        ),
        sa.CheckConstraint("balance >= 0", name="ck_wallets_balance_non_negative"),
    )


def downgrade() -> None:
    op.drop_table("wallets")
