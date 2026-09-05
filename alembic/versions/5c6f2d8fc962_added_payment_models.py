"""Added Payment Models

Revision ID: 5c6f2d8fc962
Revises: 86b4e89d95ec
Create Date: 2024-04-28 14:10:07.625228

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5c6f2d8fc962"
down_revision = "86b4e89d95ec"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "officerpayments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payment", sa.Integer(), nullable=True),
        sa.Column("officer", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["officer"], ["officers.id"], name="fk_officerpayments_officers_id_officer"
        ),
        sa.ForeignKeyConstraint(
            ["payment"], ["payments.id"], name="fk_officerpayments_payments_id_payment"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("officerpayments")
    op.drop_table("payments")
