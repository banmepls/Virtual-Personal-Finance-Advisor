"""002_add_bank_budget_tables

Revision ID: 002_bank_budget
Revises: (auto-detect previous)
Create Date: 2026-04-07

Adds:
  - bt_connections   (BT PSD2 OAuth2 consent per user)
  - bank_transactions (cached BT transaction data)
  - budgets           (user monthly category budgets)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "002_bank_budget"
down_revision = None   # Will be auto-set by alembic to the latest existing head
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bt_connections",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("consent_id", sa.String(256), nullable=True),
        sa.Column("access_token", sa.Text, nullable=True),
        sa.Column("refresh_token", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("selected_accounts", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_sandbox", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )

    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("account_id", sa.String(128), nullable=False, index=True),
        sa.Column("transaction_id", sa.String(256), unique=True, nullable=False),
        sa.Column("booking_date", sa.Date, nullable=True),
        sa.Column("value_date", sa.Date, nullable=True),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(8), default="RON"),
        sa.Column("creditor_name", sa.String(256), nullable=True),
        sa.Column("debtor_name", sa.String(256), nullable=True),
        sa.Column("remittance_info", sa.Text, nullable=True),
        sa.Column("category", sa.String(64), default="Other"),
        sa.Column("is_recurring", sa.Boolean, default=False),
        sa.Column("is_debit", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("month_year", sa.String(7), nullable=False),
        sa.Column("limit_amount", sa.Float, nullable=False),
        sa.Column("currency", sa.String(8), default="RON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_table("bank_transactions")
    op.drop_table("bt_connections")
