from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine
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


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
