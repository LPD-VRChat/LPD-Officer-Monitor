"""officer add extra column

Revision ID: dccc7b577d9a
Revises: 5c6f2d8fc962
Create Date: 2025-07-14 15:53:40.195388

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "dccc7b577d9a"
down_revision = "5c6f2d8fc962"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "officers",
        sa.Column(
            "extra",
            sa.JSON(none_as_null=True),
            nullable=True,
            default={},
        ),
    )


def downgrade():
    op.drop_column("officers", "extra")
