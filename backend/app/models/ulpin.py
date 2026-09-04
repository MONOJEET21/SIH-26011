import json
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base
from datetime import datetime


class ULPIN(Base):
    __tablename__ = "ulpins"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    ulpin: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    entity_id: Mapped[int] = mapped_column(
        nullable=False
    )

    parent_ulpin: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    hierarchy_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
