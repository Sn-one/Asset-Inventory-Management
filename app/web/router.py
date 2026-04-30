from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token, decode_token, verify_password
from app.db.models import Asset, User
from app.schemas.asset import CATEGORIES, AssetStatus
from app.services.asset_service import can_transition

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _get_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        return db.query(User).filter(User.email == email).first() if email else None
    except ValueError:
        return None


def _require_user(request: Request, db: Session) -> User | RedirectResponse:
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user


def _ctx(request: Request, user: User, **kwargs) -> dict:
    return {"request": request, "user": user, **kwargs}


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse(url="/home", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.cookies.get("access_token"):
        return RedirectResponse(url="/home", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "year": datetime.now().year})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password", "year": datetime.now().year},
            status_code=401,
        )
    token = create_access_token(user.email)
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    assets = db.query(Asset).order_by(Asset.id.desc()).all()
    stats = {
        "total":     len(assets),
        "in_stock":  sum(1 for a in assets if a.status == "in_stock"),
        "assigned":  sum(1 for a in assets if a.status == "assigned"),
        "in_repair": sum(1 for a in assets if a.status == "in_repair"),
        "retired":   sum(1 for a in assets if a.status == "retired"),
        "disposed":  sum(1 for a in assets if a.status == "disposed"),
    }
    recent = assets[:5]

    return templates.TemplateResponse("home.html", _ctx(
        request, user,
        stats=stats,
        recent=recent,
        active_page="home",
    ))


# ---------------------------------------------------------------------------
# Assets — list
# ---------------------------------------------------------------------------

@router.get("/assets", response_class=HTMLResponse)
def assets_list(
    request: Request,
    q: str = "",
    status: str = "",
    category: str = "",
    page: int = 1,
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    per_page = 15
    query = db.query(Asset)

    if q:
        like = f"%{q}%"
        query = query.filter(
            Asset.asset_tag.ilike(like)
            | Asset.name.ilike(like)
            | Asset.serial_no.ilike(like)
            | Asset.brand.ilike(like)
        )
    if status:
        query = query.filter(Asset.status == status)
    if category:
        query = query.filter(Asset.category == category)

    total = query.count()
    import math
    pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, pages))
    assets = query.order_by(Asset.id.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse("assets/list.html", _ctx(
        request, user,
        assets=assets,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page,
        q=q,
        status_filter=status,
        category_filter=category,
        categories=CATEGORIES,
        statuses=list(AssetStatus),
        active_page="assets",
    ))


# ---------------------------------------------------------------------------
# Assets — create
# ---------------------------------------------------------------------------

@router.get("/assets/new", response_class=HTMLResponse)
def asset_new(request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("assets/new.html", _ctx(
        request, user,
        categories=CATEGORIES,
        active_page="assets",
    ))


@router.post("/assets")
def asset_create(
    request: Request,
    asset_tag: str = Form(...),
    name: str = Form(""),
    brand: str = Form(""),
    model_no: str = Form(""),
    serial_no: str = Form(""),
    category: str = Form(""),
    department: str = Form(""),
    location: str = Form(""),
    assigned_to: str = Form(""),
    purchase_date: str = Form(""),
    purchase_cost: str = Form(""),
    warranty_expiry: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if db.query(Asset).filter(Asset.asset_tag == asset_tag).first():
        return templates.TemplateResponse("assets/new.html", _ctx(
            request, user,
            categories=CATEGORIES,
            active_page="assets",
            error=f"Asset tag '{asset_tag}' already exists",
            form=request,
        ), status_code=400)

    def _date(s: str) -> date | None:
        return date.fromisoformat(s) if s else None

    def _float(s: str) -> float | None:
        try:
            return float(s) if s else None
        except ValueError:
            return None

    asset = Asset(
        asset_tag=asset_tag.strip(),
        name=name.strip() or None,
        brand=brand.strip() or None,
        model_no=model_no.strip() or None,
        serial_no=serial_no.strip() or None,
        category=category or None,
        department=department.strip() or None,
        location=location.strip() or None,
        assigned_to=assigned_to.strip() or None,
        purchase_date=_date(purchase_date),
        purchase_cost=_float(purchase_cost),
        warranty_expiry=_date(warranty_expiry),
        notes=notes.strip() or None,
        status=AssetStatus.IN_STOCK.value,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return RedirectResponse(url=f"/assets/{asset.id}?success=Asset+created", status_code=303)


# ---------------------------------------------------------------------------
# Assets — detail
# ---------------------------------------------------------------------------

@router.get("/assets/{asset_id}", response_class=HTMLResponse)
def asset_detail(asset_id: int, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return RedirectResponse(url="/assets?error=Asset+not+found", status_code=302)

    current = AssetStatus(asset.status)
    available = [s for s in AssetStatus if s != current and can_transition(current, s)]

    return templates.TemplateResponse("assets/detail.html", _ctx(
        request, user,
        asset=asset,
        available_statuses=available,
        success=request.query_params.get("success"),
        error=request.query_params.get("error"),
        active_page="assets",
    ))


# ---------------------------------------------------------------------------
# Assets — edit
# ---------------------------------------------------------------------------

@router.get("/assets/{asset_id}/edit", response_class=HTMLResponse)
def asset_edit(asset_id: int, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return RedirectResponse(url="/assets", status_code=302)

    return templates.TemplateResponse("assets/edit.html", _ctx(
        request, user,
        asset=asset,
        categories=CATEGORIES,
        active_page="assets",
    ))


@router.post("/assets/{asset_id}/update")
def asset_update(
    asset_id: int,
    request: Request,
    name: str = Form(""),
    brand: str = Form(""),
    model_no: str = Form(""),
    serial_no: str = Form(""),
    category: str = Form(""),
    department: str = Form(""),
    location: str = Form(""),
    assigned_to: str = Form(""),
    purchase_date: str = Form(""),
    purchase_cost: str = Form(""),
    warranty_expiry: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return RedirectResponse(url="/assets", status_code=302)

    def _date(s: str) -> date | None:
        return date.fromisoformat(s) if s else None

    def _float(s: str) -> float | None:
        try:
            return float(s) if s else None
        except ValueError:
            return None

    asset.name = name.strip() or None
    asset.brand = brand.strip() or None
    asset.model_no = model_no.strip() or None
    asset.serial_no = serial_no.strip() or None
    asset.category = category or None
    asset.department = department.strip() or None
    asset.location = location.strip() or None
    asset.assigned_to = assigned_to.strip() or None
    asset.purchase_date = _date(purchase_date)
    asset.purchase_cost = _float(purchase_cost)
    asset.warranty_expiry = _date(warranty_expiry)
    asset.notes = notes.strip() or None

    db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}?success=Asset+updated", status_code=303)


# ---------------------------------------------------------------------------
# Assets — status update
# ---------------------------------------------------------------------------

@router.post("/assets/{asset_id}/status")
def asset_status(
    asset_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        return RedirectResponse(url="/assets?error=Asset+not+found", status_code=303)

    try:
        new_status = AssetStatus(status)
    except ValueError:
        return RedirectResponse(url=f"/assets/{asset_id}?error=Invalid+status", status_code=303)

    if not can_transition(AssetStatus(asset.status), new_status):
        return RedirectResponse(
            url=f"/assets/{asset_id}?error=Cannot+transition+from+{asset.status}+to+{status}",
            status_code=303,
        )

    asset.status = new_status.value
    db.commit()
    return RedirectResponse(
        url=f"/assets/{asset_id}?success=Status+updated+to+{status.replace('_', '+')}",
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Assets — delete
# ---------------------------------------------------------------------------

@router.post("/assets/{asset_id}/delete")
def asset_delete(asset_id: int, request: Request, db: Session = Depends(get_db)):
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if asset:
        db.delete(asset)
        db.commit()

    return RedirectResponse(url="/assets?success=Asset+deleted", status_code=303)
