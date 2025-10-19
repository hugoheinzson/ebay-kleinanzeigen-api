"""SQLAlchemy models for persisted Kleinanzeigen listings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, Boolean


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""


JSONType = JSONB().with_variant(JSON(), "sqlite")


class Listing(Base):
    """Listing metadata stored from Kleinanzeigen scrapes."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    query_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price_amount: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    price_currency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    price_negotiable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    price_text: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    delivery: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(JSONType, nullable=True)
    location: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    seller: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    features: Mapped[Optional[List[str]]] = mapped_column(JSONType, nullable=True)
    extra_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    image_urls: Mapped[Optional[List[str]]] = mapped_column(JSONType, nullable=True)
    search_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def update_timestamps(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
