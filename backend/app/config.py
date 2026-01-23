from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "mysql+pymysql://root:@127.0.0.1:3306/panel_kryon?charset=utf8mb4"

    # Seguridad
    SECRET_KEY: str = "change-me-to-a-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://[::1]:5173,http://localhost:3000,http://127.0.0.1:3000,http://[::1]:3000"

    # Media
    MEDIA_DIR: str = "./media"

    # Superadmin inicial
    SUPERADMIN_EMAIL: str = "admin@cabina.local"
    SUPERADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
