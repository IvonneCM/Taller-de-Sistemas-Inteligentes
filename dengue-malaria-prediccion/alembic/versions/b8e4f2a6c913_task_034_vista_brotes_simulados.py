"""TASK-034: vista brotes_simulados (sustituto referencial de brotes_confirmados)

Mientras no exista una fuente de brotes confirmados (riesgo M-08), la validacion
retrospectiva puede usar esta vista: cada municipio, enfermedad y fecha con al
menos un caso confirmado desde 2026. NO es un brote epidemiologico definido
(riesgo M-04); es una aproximacion referencial (CLAUDE.md regla 1).

Se suman las fuentes para que (municipio, enfermedad, fecha) sea unico, que es la
clave que usa el modelo ORM `BroteSimulado`.

Revision ID: b8e4f2a6c913
Revises: 7c1e5d9a3b42
Create Date: 2026-10-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b8e4f2a6c913'
down_revision: Union[str, None] = '7c1e5d9a3b42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW brotes_simulados AS
        SELECT
            c.municipio_id,
            c.enfermedad_id,
            c.fecha_reporte AS fecha_confirmacion,
            SUM(c.casos_confirmados)::integer AS casos_observados
        FROM casos_epidemiologicos c
        WHERE c.fecha_reporte >= DATE '2026-01-01'
        GROUP BY c.municipio_id, c.enfermedad_id, c.fecha_reporte
        HAVING SUM(c.casos_confirmados) > 0
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS brotes_simulados")
