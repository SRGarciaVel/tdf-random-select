from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Ubicacion por defecto de la base local (ver SPECS.md paragrafo 6) - vive
# en la raiz del proyecto, gitignoreada (contiene datos reales de matches).
DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "tdf_random_select.db"


class Base(DeclarativeBase):
    pass


def get_engine(db_url: str | None = None) -> Engine:
    if db_url is None:
        db_url = f"sqlite:///{DEFAULT_DB_PATH}"
    return create_engine(db_url, echo=False)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def _ensure_columns(engine: Engine, table_name: str, columns: dict[str, str]) -> None:
    """Repara bases SQLite ya existentes a las que les falten columnas
    nuevas de un modelo - `Base.metadata.create_all()` (usado en
    init_db) solo crea TABLAS que faltan, nunca agrega columnas a una
    tabla que ya existe. Sin esto, agregar un campo nuevo a un modelo
    con datos reales ya guardados (ej. `broadcast_settings` de Seba,
    checkpoint UI-5) dejaria la base real desincronizada con el codigo -
    justo el escenario de "como se actualiza" que se charló en el chat
    antes de armar el .exe.

    `columns` es un dict nombre_columna -> definicion SQL completa (ej.
    `{"ban_timer_seconds": "INTEGER DEFAULT 30"}`). Agregar acá una
    entrada nueva cada vez que un checkpoint le sume un campo a un
    modelo que ya podria tener datos reales - no hace falta tocar nada
    si la tabla es nueva (create_all ya la crea completa).
    """
    with engine.connect() as conn:
        existing = {
            row[1] for row in conn.execute(text(f"PRAGMA table_info({table_name})"))
        }
        for column_name, column_def in columns.items():
            if column_name not in existing:
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
                    )
                )
        conn.commit()


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    # Columnas nuevas en tablas que ya podrian existir de antes con
    # datos reales - ver _ensure_columns.
    _ensure_columns(
        engine,
        "broadcast_settings",
        {
            "ban_timer_seconds": "INTEGER DEFAULT 30",
            "sponsor_logo_filename": "VARCHAR",
        },
    )
