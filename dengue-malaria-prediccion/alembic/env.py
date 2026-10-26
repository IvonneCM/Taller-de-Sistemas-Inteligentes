import os
import sys
from logging.config import fileConfig

import sqlalchemy as sa
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Permite `import app...` al correr alembic desde la raiz del backend.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base  # noqa: E402
from app import models  # noqa: E402,F401  (registra todos los modelos en Base)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# DATABASE_URL viene de la variable de entorno (NFR-005: nunca hardcodear
# credenciales en alembic.ini).
if os.environ.get("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata real de los modelos ORM, para que `alembic revision --autogenerate`
# compare el esquema de la BD contra app/models/*.py.
target_metadata = Base.metadata


def _tablas_de_extensiones(connection):
    """Tablas, vistas y secuencias que pertenecen a extensiones (PostGIS).

    autogenerate las veria como "removidas" y propondria DROP TABLE/DROP INDEX,
    lo que rompe PostGIS. Se consultan dinamicamente para no mantener una
    lista hardcodeada que dependa de la version de la extension.
    """
    filas = connection.execute(
        sa.text(
            """
            SELECT c.relname
            FROM pg_class c
            JOIN pg_depend d ON d.objid = c.oid AND d.deptype = 'e'
            JOIN pg_extension e ON e.oid = d.refobjid
            WHERE c.relkind IN ('r', 'p', 'v', 'm', 'S')
            """
        )
    )
    return {fila[0] for fila in filas}

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        tablas_extension = _tablas_de_extensiones(connection)
        # La consulta anterior abre una transaccion implicita. Cerrarla para
        # que `context.begin_transaction()` controle el commit de la migracion;
        # si no, el DDL se ejecuta y se revierte al cerrar la conexion.
        connection.rollback()

        def include_object(object_, name, type_, reflected, compare_to):
            if type_ == "table" and name in tablas_extension:
                return False
            if type_ == "index" and getattr(object_, "table", None) is not None:
                if object_.table.name in tablas_extension:
                    return False
            return True

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
