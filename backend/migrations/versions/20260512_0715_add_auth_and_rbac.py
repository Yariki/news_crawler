"""Add auth, users, teams, and ownership columns

Revision ID: 20260512_AddAuthRbac
Revises: 20260508_AddRobotsModel
Create Date: 2026-05-12 07:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260512_AddAuthRbac"
down_revision: Union[str, None] = "20260508_AddRobotsModel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("force_password_change", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "user_permission_overrides",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("permission", sa.String(length=64), nullable=False),
        sa.Column("is_allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "permission", name="uq_user_permission_override"),
    )
    op.create_index(op.f("ix_user_permission_overrides_user_id"), "user_permission_overrides", ["user_id"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("access_token_hash", sa.String(length=128), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=False),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("access_token_hash"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    op.create_index(op.f("ix_auth_sessions_access_token_hash"), "auth_sessions", ["access_token_hash"], unique=False)
    op.create_index(op.f("ix_auth_sessions_refresh_token_hash"), "auth_sessions", ["refresh_token_hash"], unique=False)
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "password_reset_tokens",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_password_reset_tokens_token_hash"), "password_reset_tokens", ["token_hash"], unique=False)
    op.create_index(op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"], unique=False)

    op.add_column("sources", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_sources_owner_id"), "sources", ["owner_id"], unique=False)
    op.create_foreign_key("fk_sources_owner_id_users", "sources", "users", ["owner_id"], ["id"], ondelete="SET NULL")

    op.add_column("monitored_keywords", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_monitored_keywords_owner_id"), "monitored_keywords", ["owner_id"], unique=False)
    op.create_foreign_key(
        "fk_monitored_keywords_owner_id_users",
        "monitored_keywords",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("articles", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_articles_owner_id"), "articles", ["owner_id"], unique=False)
    op.create_foreign_key("fk_articles_owner_id_users", "articles", "users", ["owner_id"], ["id"], ondelete="SET NULL")

    op.add_column("crawl_jobs", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_crawl_jobs_owner_id"), "crawl_jobs", ["owner_id"], unique=False)
    op.create_foreign_key("fk_crawl_jobs_owner_id_users", "crawl_jobs", "users", ["owner_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_crawl_jobs_owner_id_users", "crawl_jobs", type_="foreignkey")
    op.drop_index(op.f("ix_crawl_jobs_owner_id"), table_name="crawl_jobs")
    op.drop_column("crawl_jobs", "owner_id")

    op.drop_constraint("fk_articles_owner_id_users", "articles", type_="foreignkey")
    op.drop_index(op.f("ix_articles_owner_id"), table_name="articles")
    op.drop_column("articles", "owner_id")

    op.drop_constraint("fk_monitored_keywords_owner_id_users", "monitored_keywords", type_="foreignkey")
    op.drop_index(op.f("ix_monitored_keywords_owner_id"), table_name="monitored_keywords")
    op.drop_column("monitored_keywords", "owner_id")

    op.drop_constraint("fk_sources_owner_id_users", "sources", type_="foreignkey")
    op.drop_index(op.f("ix_sources_owner_id"), table_name="sources")
    op.drop_column("sources", "owner_id")

    op.drop_index(op.f("ix_password_reset_tokens_user_id"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_token_hash"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_refresh_token_hash"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_access_token_hash"), table_name="auth_sessions")
    op.drop_table("auth_sessions")

    op.drop_index(op.f("ix_user_permission_overrides_user_id"), table_name="user_permission_overrides")
    op.drop_table("user_permission_overrides")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("teams")

