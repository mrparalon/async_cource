"""init

Revision ID: 47f1ce1142a9
Revises: 
Create Date: 2023-08-11 22:58:24.252520

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "47f1ce1142a9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("tasks_pkey")),
    )
    op.create_index(op.f("tasks_id_idx"), "tasks", ["id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("tasks_id_idx"), table_name="tasks")
    op.drop_table("tasks")
    # ### end Alembic commands ###
