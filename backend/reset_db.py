import os
import re
from app.db import engine
from app.models import Base
from app.seed import run_seed
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

def create_database_if_not_exists():
    """Crea la base de datos si no existe (MySQL/PostgreSQL). SQLite se crea automáticamente."""
    from app.config import settings
    db_url = settings.DATABASE_URL
    
    # SQLite: no necesita crear la base de datos, se crea automáticamente
    if db_url.startswith("sqlite"):
        print("✅ SQLite: la base de datos se creará automáticamente")
        return
    
    # Extract database name from URL
    # Format: driver://user:pass@host:port/database?params
    match = re.search(r'/([^/?]+)(\?|$)', db_url)
    if not match:
        print("⚠️ Could not parse database name from URL")
        return
    
    db_name = match.group(1)
    base_url = db_url.rsplit('/', 1)[0]
    
    if db_url.startswith("postgresql"):
        # PostgreSQL: conectar a 'postgres' database para crear la nueva
        base_url = base_url + "/postgres"
        temp_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
        
        try:
            with temp_engine.connect() as conn:
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
                exists = result.fetchone() is not None
                
                if not exists:
                    print(f"📦 Creating PostgreSQL database '{db_name}'...")
                    conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                    print(f"✅ Database '{db_name}' created successfully")
                else:
                    print(f"✅ Database '{db_name}' already exists")
        except Exception as e:
            print(f"⚠️ Could not create PostgreSQL database: {e}")
        finally:
            temp_engine.dispose()
    else:
        # MySQL: conectar sin base de datos específica
        temp_engine = create_engine(base_url)
        
        try:
            with temp_engine.connect() as conn:
                result = conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
                exists = result.fetchone() is not None
                
                if not exists:
                    print(f"📦 Creating MySQL database '{db_name}'...")
                    conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                    conn.commit()
                    print(f"✅ Database '{db_name}' created successfully")
                else:
                    print(f"✅ Database '{db_name}' already exists")
        except Exception as e:
            print(f"⚠️ Could not create MySQL database: {e}")
            print("   Please create the database manually in phpMyAdmin or MySQL CLI")
        finally:
            temp_engine.dispose()

def reset_database():
    """Elimina todas las tablas y las recrea con seed inicial"""
    # First, ensure the database exists
    create_database_if_not_exists()
    
    print("🔄 Eliminando tablas...")
    Base.metadata.drop_all(bind=engine)
    
    print("📝 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    
    print("🌱 Ejecutando seed...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    run_seed(session)
    session.close()
    
    print("✅ Base de datos restaurada y seed completado")

if __name__ == "__main__":
    reset_database()