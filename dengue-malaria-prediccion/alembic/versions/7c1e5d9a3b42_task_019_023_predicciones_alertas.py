"""TASK-019 a 023: alertas, umbrales_configuracion, brotes_confirmados (+ refuerzos de predicciones)

Revision ID: 7c1e5d9a3b42
Revises: 5f6a7b8c9d01
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7c1e5d9a3b42'
down_revision: Union[str, None] = '5f6a7b8c9d01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `predicciones` la crea TASK-014 (5f6a7b8c9d01). Aqui solo se refuerza:
    # `variables_explicativas` debe ser una lista JSON (REQ-004/REQ-005) y se
    # indexa la consulta de "prediccion vigente por zona".
    op.create_check_constraint(
        'ck_prediccion_variables_es_lista',
        'predicciones',
        "jsonb_typeof(variables_explicativas) = 'array'",
    )
    op.create_index(
        'ix_predicciones_municipio_enfermedad_fecha',
        'predicciones',
        ['municipio_id', 'enfermedad_id', 'fecha_generacion'],
    )

    op.create_table(
        'alertas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prediccion_id', sa.Integer(), nullable=False),
        sa.Column('umbral_aplicado', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            'fecha_emision', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.Column('justificacion', sa.Text(), nullable=False),
        sa.CheckConstraint(
            'length(btrim(justificacion)) > 0',
            name='ck_alerta_justificacion_no_vacia',
        ),
        sa.CheckConstraint(
            'umbral_aplicado >= 0 AND umbral_aplicado <= 100',
            name='ck_alerta_umbral_0_100',
        ),
        sa.ForeignKeyConstraint(['prediccion_id'], ['predicciones.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'umbrales_configuracion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enfermedad_id', sa.Integer(), nullable=False),
        sa.Column('departamento_id', sa.Integer(), nullable=True),
        sa.Column(
            'umbral_probabilidad_pct', sa.Numeric(precision=5, scale=2), nullable=False,
        ),
        sa.CheckConstraint(
            'umbral_probabilidad_pct >= 0 AND umbral_probabilidad_pct <= 100',
            name='ck_umbral_0_100',
        ),
        sa.ForeignKeyConstraint(['departamento_id'], ['departamentos.id'], ),
        sa.ForeignKeyConstraint(['enfermedad_id'], ['enfermedades.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'enfermedad_id', 'departamento_id',
            name='uq_umbral_enfermedad_departamento',
            postgresql_nulls_not_distinct=True,
        ),
    )

    op.create_table(
        'brotes_confirmados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('municipio_id', sa.Integer(), nullable=False),
        sa.Column('enfermedad_id', sa.Integer(), nullable=False),
        sa.Column('fecha_confirmacion', sa.Date(), nullable=False),
        sa.Column('fuente', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['enfermedad_id'], ['enfermedades.id'], ),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('brotes_confirmados')
    op.drop_table('umbrales_configuracion')
    op.drop_table('alertas')
    op.drop_index('ix_predicciones_municipio_enfermedad_fecha', table_name='predicciones')
    op.drop_constraint('ck_prediccion_variables_es_lista', 'predicciones', type_='check')
