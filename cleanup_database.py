from sqlalchemy import text

from backend.app.db.database import engine

tables = [
    "validation_issues",
    "ulpins",
    "property_units",
    "floors",
    "underground_assets",
    "buildings",
    "parcels",
    "study_areas",
]

with engine.begin() as connection:
    for table in tables:
        connection.execute(text(f'DELETE FROM "{table}"'))

print("Database test data deleted successfully.")
