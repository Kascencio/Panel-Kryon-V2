import os
import re
from app.db import engine
from app.models import Base
from app.seed import run_seed
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

def create_database_if_not_exists():
    """Crea la base de datos si no existe"""
    # Get the DATABASE_URL from environment or config
    from app.config import settings
    db_url = settings.DATABASE_URL
    
    # Extract database name from URL
    # Format: mysql+pymysql://user:pass@host:port/database?params
    match = re.search(r'/([^/?]+)(\?|$)', db_url)
    if not match:
        print("⚠️ Could not parse database name from URL")
        return
    
    db_name = match.group(1)
    
    # Create a connection URL without the database name
    base_url = db_url.rsplit('/', 1)[0]
    
    # Connect to MySQL server (without specific database)
    temp_engine = create_engine(base_url)
    
    try:
        with temp_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"📦 Creating database '{db_name}'...")
                conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
                print(f"✅ Database '{db_name}' created successfully")
            else:
                print(f"✅ Database '{db_name}' already exists")
    except Exception as e:
        print(f"⚠️ Could not create database automatically: {e}")
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