from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_assets() -> dict[str, list]:
    return {"items": []}
