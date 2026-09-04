from sqlalchemy import ForeignKey, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from app.db.database import Base
from datetime import datetime


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    study_area_id: Mapped[int] = mapped_column(
        ForeignKey("study_areas.id"),
        nullable=False
    )

    parcel_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    parcel_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    area = mapped_column(Float, nullable=False)

    land_use: Mapped[str] = mapped_column(
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