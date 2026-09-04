from sqlalchemy import ForeignKey, String, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from app.db.database import Base
from datetime import datetime

class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcels.id"),
        nullable=False
    )

    building_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    building_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    ground_elevation: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    height: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    floor_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    building_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE"
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