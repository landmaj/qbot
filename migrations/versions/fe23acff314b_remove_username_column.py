"""remove username column

Revision ID: fe23acff314b
Revises: 164f07c07d3b
Create Date: 2020-05-01 15:22:34.874220

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fe23acff314b"
down_revision = "164f07c07d3b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("credentials", "username")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "credentials",
        sa.Column("username", sa.TEXT(), autoincrement=False, nullable=False),
    )
    # ### end Alembic commands ###
