"""TASK-014: tabla predicciones

Revision ID: 5f6a7b8c9d01
Revises: aa12e214cb8d
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5f6a7b8c9d01'
down_revision: Union[str, None] = 'aa12e214cb8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'predicciones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('municipio_id', sa.Integer(), nullable=False),
        sa.Column('enfermedad_id', sa.Integer(), nullable=False),
        sa.Column('modelo_id', sa.Integer(), nullable=False),
        sa.Column(
            'fecha_generacion',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('fecha_estimada_riesgo', sa.Date(), nullable=False),
        sa.Column('nivel_riesgo', sa.String(length=10), nullable=False),
        sa.Column('probabilidad_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('nivel_confianza', sa.String(length=10), nullable=False),
        sa.Column(
            'variables_explicativas',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.CheckConstraint(
            'probabilidad_pct >= 0 AND probabilidad_pct <= 100',
            name='ck_prediccion_probabilidad_0_100',
        ),
        sa.CheckConstraint(
            "nivel_riesgo IN ('bajo', 'medio', 'alto')",
            name='ck_prediccion_nivel_riesgo',
        ),
        sa.CheckConstraint(
            "nivel_confianza IN ('bajo', 'medio', 'alto')",
            name='ck_prediccion_nivel_confianza',
        ),
        sa.CheckConstraint(
            'fecha_estimada_riesgo BETWEEN '
            "((fecha_generacion AT TIME ZONE 'UTC')::date + 21) AND "
            "((fecha_generacion AT TIME ZONE 'UTC')::date + 28)",
            name='ck_prediccion_horizonte_21_28_dias',
        ),
        sa.ForeignKeyConstraint(['enfermedad_id'], ['enfermedades.id'], ),
        sa.ForeignKeyConstraint(['modelo_id'], ['modelos.id'], ),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('predicciones')
