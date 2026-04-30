import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure schema and seed data exist before any fixture touches the DB directly.
from app.core.security import get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models import Role, User  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import _ASSET_MIGRATIONS, _LOCATION_MIGRATIONS, _migrate_columns, _seed_rfid_index  # noqa: E402

Base.metadata.create_all(bind=engine)
_migrate_columns("assets", _ASSET_MIGRATIONS)
_migrate_columns("locations", _LOCATION_MIGRATIONS)
_seed_rfid_index()

_db = SessionLocal()
try:
    if not _db.query(Role).filter(Role.name == "admin").first():
        _db.add(Role(name="admin"))
    if not _db.query(User).filter(User.email == "admin@example.com").first():
        _db.add(User(
            email="admin@example.com",
            full_name="Admin User",
            password_hash=get_password_hash("admin123"),
            is_active=True,
        ))
    _db.commit()
finally:
    _db.close()
