"""Add article FK to keyword_hits

Revision ID: 20260421_KeywordHitArticleFk
Revises: 20260412_InitialSchema
Create Date: 2026-04-21

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260421_KeywordHitArticleFk"
down_revision: Union[str, None] = "20260412_InitialSchema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "keyword_hits",
        sa.Column("article_id", sa.Uuid(), nullable=False),
    )
    op.create_index(
        "ix_keyword_hits_article_id",
        "keyword_hits",
        ["article_id"],
    )
    op.create_foreign_key(
        "fk_keyword_hits_article_id_articles",
        "keyword_hits",
        "articles",
        ["article_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_keyword_hits_article_id_articles",
        "keyword_hits",
        type_="foreignkey",
    )
    op.drop_index("ix_keyword_hits_article_id", table_name="keyword_hits")
    op.drop_column("keyword_hits", "article_id")
