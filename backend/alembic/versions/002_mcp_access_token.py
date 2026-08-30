"""Add mcp_access_token to merchants.

Revision ID: 002_mcp_access_token
Revises: 001_initial
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_mcp_access_token"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("mcp_access_token", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_merchants_mcp_access_token", "merchants", ["mcp_access_token"])


def downgrade() -> None:
    op.drop_constraint("uq_merchants_mcp_access_token", "merchants", type_="unique")
    op.drop_column("merchants", "mcp_access_token")
