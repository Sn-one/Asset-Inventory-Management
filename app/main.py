from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import Role, User
from app.db.session import SessionLocal, engine
from app.web.router import router as web_router

# New nullable columns added to assets table — safe to apply on existing DBs
_ASSET_MIGRATIONS = [
    ("name",           "VARCHAR(128)"),
    ("brand",          "VARCHAR(64)"),
    ("model_no",       "VARCHAR(128)"),
    ("department",     "VARCHAR(64)"),
    ("assigned_to",    "VARCHAR(128)"),
    ("purchase_date",  "DATE"),
    ("purchase_cost",  "FLOAT"),
    ("warranty_expiry","DATE"),
    ("notes",          "TEXT"),
    ("created_at",     "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ("updated_at",     "DATETIME DEFAULT CURRENT_TIMESTAMP"),
]


def _migrate_asset_columns() -> None:
    with engine.connect() as conn:
        for col, col_type in _ASSET_MIGRATIONS:
            try:
                conn.execute(text(f"ALTER TABLE assets ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # column already exists


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)
        _migrate_asset_columns()

        db = SessionLocal()
        try:
            if not db.query(Role).filter(Role.name == "admin").first():
                db.add(Role(name="admin"))
            if not db.query(User).filter(User.email == "admin@example.com").first():
                db.add(
                    User(
                        email="admin@example.com",
                        full_name="Admin User",
                        password_hash=get_password_hash("admin123"),
                        is_active=True,
                    )
                )
            db.commit()
        finally:
            db.close()

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(web_router)
    return app


app = create_app()
