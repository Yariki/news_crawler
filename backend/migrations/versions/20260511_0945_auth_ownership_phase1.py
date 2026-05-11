"""Add auth, ownership, and session tables

Revision ID: 20260511_0945_AuthOwnership
Revises: 20260508_AddRobotsModel
Create Date: 2026-05-11 09:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260511_0945_AuthOwnership"
down_revision: Union[str, None] = "20260508_AddRobotsModel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], unique=False)
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission", sa.String(length=100), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission", name="uq_role_permissions_role_permission"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("family_id", sa.String(length=64), nullable=False),
        sa.Column("parent_token_id", sa.Uuid(), nullable=True),
        sa.Column("replaced_by_token_id", sa.Uuid(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_token_id"], ["refresh_tokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["replaced_by_token_id"], ["refresh_tokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"], unique=False)
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)

    op.add_column("sources", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_sources_owner_id_users", "sources", "users", ["owner_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_sources_owner_id", "sources", ["owner_id"], unique=False)

    op.add_column("monitored_keywords", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_monitored_keywords_owner_id_users", "monitored_keywords", "users", ["owner_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_monitored_keywords_owner_id", "monitored_keywords", ["owner_id"], unique=False)
    op.drop_constraint("monitored_keywords_keyword_key", "monitored_keywords", type_="unique")
    op.create_unique_constraint("uq_monitored_keywords_owner_keyword", "monitored_keywords", ["owner_id", "keyword"])

    op.add_column("articles", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_articles_owner_id_users", "articles", "users", ["owner_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_articles_owner_id", "articles", ["owner_id"], unique=False)

    op.add_column("crawl_jobs", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_crawl_jobs_owner_id_users", "crawl_jobs", "users", ["owner_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_crawl_jobs_owner_id", "crawl_jobs", ["owner_id"], unique=False)

    op.execute(
        """
        INSERT INTO users (email, password_hash, is_active)
        VALUES (
            'admin@news-crawler.local',
            'pbkdf2_sha256$310000$newsmonitorseed$MBMWdU5_ONGrL7DLuwOauOK8deZCNdxIIPF6UOPAD-s',
            true
        )
        ON CONFLICT (email) DO NOTHING
        """
    )
    op.execute("INSERT INTO roles (name) VALUES ('admin') ON CONFLICT (name) DO NOTHING")
    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission)
        SELECT r.id, p.permission
        FROM roles r
        CROSS JOIN (VALUES
            ('users:read'),
            ('users:write'),
            ('roles:read'),
            ('roles:write'),
            ('audit:read')
        ) p(permission)
        WHERE r.name = 'admin'
        ON CONFLICT (role_id, permission) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id
        FROM users u
        JOIN roles r ON r.name = 'admin'
        WHERE u.email = 'admin@news-crawler.local'
        ON CONFLICT (user_id, role_id) DO NOTHING
        """
    )

    op.execute("UPDATE sources SET owner_id = (SELECT id FROM users WHERE email='admin@news-crawler.local' LIMIT 1)")
    op.execute(
        "UPDATE monitored_keywords SET owner_id = (SELECT id FROM users WHERE email='admin@news-crawler.local' LIMIT 1)"
    )
    op.execute("UPDATE articles SET owner_id = (SELECT id FROM users WHERE email='admin@news-crawler.local' LIMIT 1)")
    op.execute("UPDATE crawl_jobs SET owner_id = (SELECT id FROM users WHERE email='admin@news-crawler.local' LIMIT 1)")

    op.alter_column("sources", "owner_id", nullable=False)
    op.alter_column("monitored_keywords", "owner_id", nullable=False)
    op.alter_column("articles", "owner_id", nullable=False)
    op.alter_column("crawl_jobs", "owner_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_crawl_jobs_owner_id", table_name="crawl_jobs")
    op.drop_constraint("fk_crawl_jobs_owner_id_users", "crawl_jobs", type_="foreignkey")
    op.drop_column("crawl_jobs", "owner_id")

    op.drop_index("ix_articles_owner_id", table_name="articles")
    op.drop_constraint("fk_articles_owner_id_users", "articles", type_="foreignkey")
    op.drop_column("articles", "owner_id")

    op.drop_constraint("uq_monitored_keywords_owner_keyword", "monitored_keywords", type_="unique")
    op.create_unique_constraint("monitored_keywords_keyword_key", "monitored_keywords", ["keyword"])
    op.drop_index("ix_monitored_keywords_owner_id", table_name="monitored_keywords")
    op.drop_constraint("fk_monitored_keywords_owner_id_users", "monitored_keywords", type_="foreignkey")
    op.drop_column("monitored_keywords", "owner_id")

    op.drop_index("ix_sources_owner_id", table_name="sources")
    op.drop_constraint("fk_sources_owner_id_users", "sources", type_="foreignkey")
    op.drop_column("sources", "owner_id")

    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
