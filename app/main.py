from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import Asset, Location, RFIDReader, Role, User, UserRole
from app.db.session import SessionLocal, engine
from app.schemas.asset import CATEGORY_CODES
from app.web.router import router as web_router

_ASSET_MIGRATIONS = [
    ("name",                    "VARCHAR(128)"),
    ("brand",                   "VARCHAR(64)"),
    ("model_no",                "VARCHAR(128)"),
    ("department",              "VARCHAR(64)"),
    ("assigned_to",             "VARCHAR(128)"),
    ("purchase_date",           "DATE"),
    ("purchase_cost",           "FLOAT"),
    ("warranty_expiry",         "DATE"),
    ("notes",                   "TEXT"),
    ("created_at",              "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ("updated_at",              "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ("site_id",                 "INTEGER REFERENCES locations(id)"),
    ("rfid_tag",                "VARCHAR(64)"),
    ("rfid_last_seen",          "DATETIME"),
    ("rfid_confirmed_site_id",  "INTEGER REFERENCES locations(id)"),
]

_LOCATION_MIGRATIONS = [
    ("address",   "VARCHAR(200)"),
    ("latitude",  "FLOAT"),
    ("longitude", "FLOAT"),
]

_USER_MIGRATIONS = [
    ("site_id", "INTEGER REFERENCES locations(id)"),
]

_GHANA_STATIONS = [
    {"name": "Accra Central Station",  "code": "ACC", "address": "Ring Road Central, Accra",    "latitude":  5.5502, "longitude": -0.2174},
    {"name": "Tema Station",           "code": "TEM", "address": "Community 1, Tema",            "latitude":  5.6698, "longitude": -0.0166},
    {"name": "Kumasi Central Station", "code": "KUM", "address": "Adum, Kumasi",                  "latitude":  6.6885, "longitude": -1.6244},
    {"name": "Takoradi Station",       "code": "TAK", "address": "Market Circle, Takoradi",       "latitude":  4.8985, "longitude": -1.7582},
    {"name": "Tamale Station",         "code": "TAM", "address": "Central Tamale",                "latitude":  9.4075, "longitude": -0.8533},
    {"name": "Cape Coast Station",     "code": "CAP", "address": "Commercial Street, Cape Coast", "latitude":  5.1037, "longitude": -1.2827},
    {"name": "Sunyani Station",        "code": "SUN", "address": "Sunyani Town Centre",           "latitude":  7.3349, "longitude": -2.3123},
    {"name": "Koforidua Station",      "code": "KOF", "address": "Koforidua Central",             "latitude":  6.0942, "longitude": -0.2574},
    {"name": "Ho Station",             "code": "HO",  "address": "Ho Township",                  "latitude":  6.6012, "longitude":  0.4707},
    {"name": "Bolgatanga Station",     "code": "BOL", "address": "Bolgatanga Town",              "latitude": 10.7855, "longitude": -0.8514},
    {"name": "Wa Station",             "code": "WA",  "address": "Wa Town Centre",               "latitude": 10.0601, "longitude": -2.5099},
    {"name": "Techiman Station",       "code": "TEC", "address": "Techiman Market Area",          "latitude":  7.5899, "longitude": -1.9396},
    {"name": "Obuasi Station",         "code": "OBU", "address": "Obuasi Mine Road",             "latitude":  6.2030, "longitude": -1.6641},
    {"name": "Winneba Station",        "code": "WIN", "address": "Winneba Town",                  "latitude":  5.3586, "longitude": -0.6283},
    {"name": "Berekum Station",        "code": "BER", "address": "Berekum Market",               "latitude":  7.4522, "longitude": -2.5850},
    {"name": "Agona Swedru Station",   "code": "AGO", "address": "Agona Swedru Central",         "latitude":  5.5347, "longitude": -0.7026},
    {"name": "Dunkwa Station",         "code": "DUN", "address": "Dunkwa-on-Offin",             "latitude":  5.9747, "longitude": -1.7808},
    {"name": "Nkawkaw Station",        "code": "NKA", "address": "Nkawkaw Central",             "latitude":  6.5541, "longitude": -0.7622},
    {"name": "Hohoe Station",          "code": "HOH", "address": "Hohoe Township",              "latitude":  7.1525, "longitude":  0.4757},
    {"name": "Navrongo Station",       "code": "NAV", "address": "Navrongo Central",            "latitude": 10.8942, "longitude": -1.0918},
]

# 7 assets seeded per station (category, name, brand, status, rfid suffix or None)
_STATION_ASSET_TEMPLATES = [
    ("Fuel Dispenser",              "Multi-Product Dispenser",    "Gilbarco Veeder-Root", "in_service",        "FD-A"),
    ("Fuel Dispenser",              "Single-Product Dispenser",   "Wayne Fueling",        "in_service",        "FD-B"),
    ("Underground Storage Tank",    "20,000L Petrol Storage Tank","Xerxes",               "in_service",        None),
    ("Generator Set",               "100kVA Backup Generator",    "CAT",                  "in_service",        "GEN"),
    ("IT & POS Equipment",          "POS Terminal",               "Ingenico",             "in_service",        None),
    ("Safety & Fire Equipment",     "CO2 Fire Extinguisher",      "Amerex",               "in_service",        None),
    ("CCTV & Security",             "IP Dome Camera",             "Hikvision",            "in_service",        None),
]

_ALL_ROLES = [
    "admin",
    "viewer",
    "asset_manager",
    "maintenance_supervisor",
    "maintenance_manager",
]

_DEMO_USERS = [
    {"email": "manager.accra@example.com",  "full_name": "Kwame Mensah",   "role": "asset_manager",         "site_code": "ACC", "password": "demo1234"},
    {"email": "manager.kumasi@example.com", "full_name": "Abena Boateng",  "role": "asset_manager",         "site_code": "KUM", "password": "demo1234"},
    {"email": "maint.manager@example.com",  "full_name": "Kofi Asante",    "role": "maintenance_manager",   "site_code": None,  "password": "demo1234"},
    {"email": "maint.sup.tema@example.com", "full_name": "Ama Darko",      "role": "maintenance_supervisor","site_code": "TEM", "password": "demo1234"},
    {"email": "viewer@example.com",         "full_name": "Yaw Owusu",      "role": "viewer",                "site_code": None,  "password": "demo1234"},
]


def _migrate_columns(table: str, columns: list[tuple[str, str]]) -> None:
    with engine.connect() as conn:
        for col, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass


def _seed_rfid_index() -> None:
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_assets_rfid_tag "
                "ON assets (rfid_tag) WHERE rfid_tag IS NOT NULL"
            ))
            conn.commit()
        except Exception:
            pass


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)
        _migrate_columns("assets", _ASSET_MIGRATIONS)
        _migrate_columns("locations", _LOCATION_MIGRATIONS)
        _migrate_columns("users", _USER_MIGRATIONS)
        _seed_rfid_index()

        db = SessionLocal()
        try:
            # Roles
            for rname in _ALL_ROLES:
                if not db.query(Role).filter(Role.name == rname).first():
                    db.add(Role(name=rname))
            db.flush()

            # Admin user
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            admin = db.query(User).filter(User.email == "admin@example.com").first()
            if not admin:
                admin = User(
                    email="admin@example.com",
                    full_name="Admin User",
                    password_hash=get_password_hash("admin123"),
                    is_active=True,
                )
                db.add(admin)
                db.flush()
            if admin_role and not db.query(UserRole).filter(UserRole.user_id == admin.id).first():
                db.add(UserRole(user_id=admin.id, role_id=admin_role.id))

            # Ghana station seeds
            for s in _GHANA_STATIONS:
                if not db.query(Location).filter(Location.code == s["code"]).first():
                    db.add(Location(
                        name=s["name"], code=s["code"],
                        address=s["address"], latitude=s["latitude"], longitude=s["longitude"],
                    ))
            db.flush()

            # RFID readers per station + mobile readers
            for s in _GHANA_STATIONS:
                loc = db.query(Location).filter(Location.code == s["code"]).first()
                if loc:
                    reader_code = f"SR-{s['code']}-01"
                    if not db.query(RFIDReader).filter(RFIDReader.reader_code == reader_code).first():
                        db.add(RFIDReader(
                            name=f"{s['name']} Gate Reader", reader_code=reader_code,
                            reader_type="stationary", site_id=loc.id, is_active=True,
                        ))
            for i, code in enumerate(["MR-001", "MR-002"], start=1):
                if not db.query(RFIDReader).filter(RFIDReader.reader_code == code).first():
                    db.add(RFIDReader(
                        name=f"Mobile Audit Reader {i:02d}", reader_code=code,
                        reader_type="mobile", site_id=None, is_active=True,
                    ))
            db.flush()

            # Sample assets per station
            for s in _GHANA_STATIONS:
                loc = db.query(Location).filter(Location.code == s["code"]).first()
                if not loc:
                    continue
                for idx, (cat, name, brand, status, rfid_suffix) in enumerate(_STATION_ASSET_TEMPLATES, start=1):
                    cat_code = CATEGORY_CODES.get(cat, "OTH")
                    tag = f"{cat_code}-{s['code']}-{idx:04d}"
                    if db.query(Asset).filter(Asset.asset_tag == tag).first():
                        continue
                    rfid = f"RFID-{s['code']}-{rfid_suffix}" if rfid_suffix else None
                    db.add(Asset(
                        asset_tag=tag,
                        name=f"{s['name']} — {name}",
                        brand=brand,
                        category=cat,
                        status=status,
                        site_id=loc.id,
                        location=loc.name,
                        rfid_tag=rfid,
                    ))
            db.flush()

            # Demo users
            for u in _DEMO_USERS:
                role = db.query(Role).filter(Role.name == u["role"]).first()
                site = db.query(Location).filter(Location.code == u["site_code"]).first() if u["site_code"] else None
                existing = db.query(User).filter(User.email == u["email"]).first()
                if not existing:
                    new_user = User(
                        email=u["email"],
                        full_name=u["full_name"],
                        password_hash=get_password_hash(u["password"]),
                        is_active=True,
                        site_id=site.id if site else None,
                    )
                    db.add(new_user)
                    db.flush()
                    if role:
                        db.add(UserRole(user_id=new_user.id, role_id=role.id))

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
