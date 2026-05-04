from pathlib import Path

from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "sqlite:///./panel_kryon.db"

    # Seguridad
    SECRET_KEY: str = "ac22702b61078d0455e3ba171acc2d3c"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    # Media
    MEDIA_DIR: str = "./media"

    # Superadmin inicial
    SUPERADMIN_EMAIL: str = "admin@panel.com"
    SUPERADMIN_PASSWORD: str = "admin123"

    class Config:
        # Always resolve the backend .env from the package location, not the cwd.
        env_file = str(BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
