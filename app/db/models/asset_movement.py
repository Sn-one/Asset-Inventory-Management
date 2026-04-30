from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetMovement(Base):
    __tablename__ = "asset_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    from_site_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    to_site_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    pemo_number: Mapped[str] = mapped_column(String(64), nullable=False)
    pemo_document_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    moved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    asset: Mapped[Asset] = relationship("Asset", foreign_keys=[asset_id], lazy="select")
    from_site: Mapped[Location | None] = relationship("Location", foreign_keys=[from_site_id], lazy="select")
    to_site: Mapped[Location | None] = relationship("Location", foreign_keys=[to_site_id], lazy="select")
    moved_by: Mapped[User | None] = relationship("User", foreign_keys=[moved_by_id], lazy="select")
