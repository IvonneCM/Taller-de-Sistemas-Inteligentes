"""TASK-012: tabla modelos

Revision ID: 4079b097a5a2
Revises: 2a95c198fba5
Create Date: 2026-10-25 23:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4079b097a5a2'
down_revision: Union[str, None] = '2a95c198fba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'modelos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('enfermedad_id', sa.Integer(), nullable=True),
        sa.Column('fecha_entrenamiento', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'metricas_entrenamiento',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(['enfermedad_id'], ['enfermedades.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('modelos')
