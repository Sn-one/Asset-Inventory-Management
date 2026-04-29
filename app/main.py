from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import Role, User
from app.db.session import SessionLocal, engine


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)
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
    return app


app = create_app()
