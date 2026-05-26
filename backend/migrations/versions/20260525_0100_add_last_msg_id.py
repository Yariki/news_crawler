"""Add last_message_id to sources

Revision ID: 20260525_AddLastMsgId
Revises: 20260508_AddRobotsModel
Create Date: 2026-05-25 01:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260525_AddLastMsgId"
down_revision: Union[str, None] = "20260508_AddRobotsModel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("last_message_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("sources", "last_message_id")
