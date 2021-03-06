"""init

Revision ID: f32a45256434
Revises: 
Create Date: 2019-09-18 20:52:51.036147

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f32a45256434"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "nosacze",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nosacze")),
        sa.UniqueConstraint("url", name=op.f("uq_nosacze_url")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("nosacze")
    # ### end Alembic commands ###
