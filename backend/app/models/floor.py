from sqlalchemy import ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from backend.app.db.database import Base
from datetime import datetime


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    building_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id"),
        nullable=False
    )

    level_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    z_min: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    z_max: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="POLYGON",
            srid=4326,
            spatial_index=False
        ),
        nullable=False
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
