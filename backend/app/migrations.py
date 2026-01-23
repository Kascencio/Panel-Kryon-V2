from sqlalchemy import inspect, text

from .db import Base, engine


def _add_column_if_missing(conn, table: str, column: str, ddl: str, backfill_sql: list[str] | None = None) -> None:
    existing_cols = {c["name"] for c in inspect(conn).get_columns(table)}
    if column in existing_cols:
        return

    conn.execute(text(ddl))
    if backfill_sql:
        for stmt in backfill_sql:
            conn.execute(text(stmt))


def run_migrations() -> bool:
    """Migraciones ligeras (sin Alembic). Idempotentes."""
    try:
        # Crear tablas faltantes
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        if not inspector.has_table("therapies"):
            return True

        with engine.begin() as conn:
            _add_column_if_missing(
                conn,
                "therapies",
                "default_intensity",
                "ALTER TABLE therapies ADD COLUMN default_intensity INT DEFAULT 50",
                [
                    "UPDATE therapies SET default_intensity = 50 WHERE default_intensity IS NULL",
                ],
            )

            _add_column_if_missing(
                conn,
                "therapies",
                "audio_corto_path",
                "ALTER TABLE therapies ADD COLUMN audio_corto_path VARCHAR(500) DEFAULT NULL",
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "audio_mediano_path",
                "ALTER TABLE therapies ADD COLUMN audio_mediano_path VARCHAR(500) DEFAULT NULL",
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "audio_largo_path",
                "ALTER TABLE therapies ADD COLUMN audio_largo_path VARCHAR(500) DEFAULT NULL",
            )

            _add_column_if_missing(
                conn,
                "therapies",
                "duration_corto_sec",
                "ALTER TABLE therapies ADD COLUMN duration_corto_sec INT DEFAULT 300",
                [
                    "UPDATE therapies SET duration_corto_sec = 300 WHERE duration_corto_sec IS NULL",
                ],
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "duration_mediano_sec",
                "ALTER TABLE therapies ADD COLUMN duration_mediano_sec INT DEFAULT 1200",
                [
                    "UPDATE therapies SET duration_mediano_sec = 1200 WHERE duration_mediano_sec IS NULL",
                ],
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "duration_largo_sec",
                "ALTER TABLE therapies ADD COLUMN duration_largo_sec INT DEFAULT 10800",
                [
                    "UPDATE therapies SET duration_largo_sec = 10800 WHERE duration_largo_sec IS NULL",
                ],
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "duration_labels",
                "ALTER TABLE therapies ADD COLUMN duration_labels TEXT DEFAULT NULL",
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "arduino_config",
                "ALTER TABLE therapies ADD COLUMN arduino_config TEXT DEFAULT NULL",
            )

            _add_column_if_missing(
                conn,
                "therapies",
                "media_type",
                "ALTER TABLE therapies ADD COLUMN media_type VARCHAR(10)",
                [
                    """
                    UPDATE therapies
                    SET media_type = CASE
                        WHEN video_path IS NOT NULL AND (
                            audio_corto_path IS NOT NULL OR audio_mediano_path IS NOT NULL OR audio_largo_path IS NOT NULL OR audio_path IS NOT NULL
                        ) THEN 'both'
                        WHEN video_path IS NOT NULL THEN 'video'
                        WHEN (
                            audio_corto_path IS NOT NULL OR audio_mediano_path IS NOT NULL OR audio_largo_path IS NOT NULL OR audio_path IS NOT NULL
                        ) THEN 'audio'
                        ELSE 'audio'
                    END
                    WHERE media_type IS NULL
                    """,
                ],
            )
            _add_column_if_missing(
                conn,
                "therapies",
                "access_level",
                "ALTER TABLE therapies ADD COLUMN access_level VARCHAR(10)",
                [
                    "UPDATE therapies SET access_level = 'basic' WHERE access_level IS NULL",
                ],
            )
        return True
    except Exception as e:
        # No romper startup por un ALTER TABLE (por ejemplo, si la tabla aún no existe)
        print(f"⚠️  Migraciones omitidas: {e}")
        return False
