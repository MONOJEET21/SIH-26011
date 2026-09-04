# ADTU Prototype Import Data

Prepared from the supplied ADTU GIS ZIP.

- Parcel source coordinates were interpreted as EPSG:32646 and transformed to EPSG:4326.
- Building source: `ADTU_Buildings_Final_2.gpkg`, transformed from EPSG:32646 to EPSG:4326.
- Study-area boundary is a prototype convex hull derived from the supplied parcel geometries.
- No floors, property units, or underground assets are included because they were not supplied.

Copy:
- `data/real/*.geojson` into the project's `data/real/`
- `backend/scripts/import_adtu_prototype.py` into the project's `backend/scripts/`
