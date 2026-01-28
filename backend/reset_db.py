import os
from app.db import engine
from app.models import Base
from app.seed import run_seed  # Cambia según el nombre real de tu función
from sqlalchemy.orm import sessionmaker

def reset_database():
    """Elimina todas las tablas y las recrea con seed inicial"""
    print("🔄 Eliminando tablas...")
    Base.metadata.drop_all(bind=engine)
    
    print("📝 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    
    print("🌱 Ejecutando seed...")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    run_seed(session)  # Usa el nombre correcto
    session.close()
    
    print("✅ Base de datos restaurada y seed completado")

if __name__ == "__main__":
    reset_database()