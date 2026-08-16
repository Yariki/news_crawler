"""Fix auth audit timestamp column types.

Revision ID: 20260817_AuthAuditTimestamps
Revises: 20260804_AddedIssuedRefreshToken
Create Date: 2026-08-17 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260817_AuthAuditTimestamps"
down_revision: Union[str, None] = "20260804_AddedIssuedRefreshToken"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AUTH_AUDIT_COLUMNS = (
    ("permissions", "created_at"),
    ("permissions", "updated_at"),
    ("roles", "created_at"),
    ("roles", "updated_at"),
    ("users", "created_at"),
    ("users", "updated_at"),
    ("role_permissions", "created_at"),
    ("role_permissions", "updated_at"),
    ("user_roles", "created_at"),
    ("user_roles", "updated_at"),
)


def upgrade() -> None:
    for table_name, column_name in AUTH_AUDIT_COLUMNS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.String(),
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column_name}::timestamptz",
        )


def downgrade() -> None:
    for table_name, column_name in AUTH_AUDIT_COLUMNS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.String(),
            postgresql_using=f"{column_name}::text",
        )
