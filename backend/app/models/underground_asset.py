from sqlalchemy import ForeignKey, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from backend.app.db.database import Base
from datetime import datetime


class UndergroundAsset(Base):
    __tablename__ = "underground_assets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    parcel_id: Mapped[int] = mapped_column(
        ForeignKey("parcels.id"),
        nullable=False
    )

    asset_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    asset_code: Mapped[str] = mapped_column(
        String(100),
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

    depth: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
    String(50),
    nullable=False,
    default="ACTIVE"
)

    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="LINESTRING",
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
