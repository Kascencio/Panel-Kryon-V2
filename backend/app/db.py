from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


def get_engine():
    """
    Crea el engine de SQLAlchemy con configuración específica según el tipo de BD.
    Soporta: SQLite, MySQL, PostgreSQL
    """
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("sqlite"):
        # SQLite: requiere check_same_thread=False para FastAPI
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
    elif db_url.startswith("postgresql"):
        # PostgreSQL: pool_pre_ping para detectar conexiones caídas
        return create_engine(db_url, pool_pre_ping=True)
    else:
        # MySQL y otros: pool_pre_ping por defecto
        return create_engine(db_url, pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para obtener sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
