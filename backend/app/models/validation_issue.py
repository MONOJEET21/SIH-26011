from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime
from geoalchemy2 import Geometry
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

   

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="PROPERTY_UNIT"
    )

    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    issue_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    geometry: Mapped[object | None] = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326,
            spatial_index=False
        ),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OPEN"
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
