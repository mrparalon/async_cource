"""accounting_user_balance

Revision ID: 355297695b93
Revises: 0c66617043bf
Create Date: 2023-08-20 16:11:24.192103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '355297695b93'
down_revision = '0c66617043bf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('accounting_users', sa.Column('balance', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('accounting_users', 'balance')
    # ### end Alembic commands ###
