from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RFIDReader(Base):
    __tablename__ = "rfid_readers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    reader_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # "stationary" — fixed at a station gate; "mobile" — handheld for audits
    reader_type: Mapped[str] = mapped_column(String(20), nullable=False, default="stationary")
    site_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    site: Mapped[Location | None] = relationship("Location", foreign_keys=[site_id], lazy="select")
