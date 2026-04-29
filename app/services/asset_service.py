from app.schemas.asset import AssetStatus

_ALLOWED_TRANSITIONS: dict[AssetStatus, set[AssetStatus]] = {
    AssetStatus.IN_STOCK: {AssetStatus.ASSIGNED, AssetStatus.IN_REPAIR, AssetStatus.RETIRED, AssetStatus.DISPOSED},
    AssetStatus.ASSIGNED: {AssetStatus.IN_STOCK, AssetStatus.IN_REPAIR, AssetStatus.RETIRED},
    AssetStatus.IN_REPAIR: {AssetStatus.IN_STOCK, AssetStatus.RETIRED, AssetStatus.DISPOSED},
    AssetStatus.RETIRED: {AssetStatus.DISPOSED},
    AssetStatus.DISPOSED: set(),
}


def can_transition(current: AssetStatus, target: AssetStatus) -> bool:
    if current == target:
        return True
    return target in _ALLOWED_TRANSITIONS[current]
