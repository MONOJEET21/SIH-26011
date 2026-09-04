# 3D ULPIN Backend

Backend API for the **AI-Assisted 3D ULPIN and Vertical Property Mapping** system.

The backend provides PostgreSQL/PostGIS storage, hierarchical property relationships, GeoJSON-based spatial APIs, ULPIN retrieval, validation issues, database migrations, and automated tests.

---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- PostGIS
- GeoAlchemy2
- Alembic
- Pydantic
- Pytest
- Uvicorn

---

## Project Structure

```text
backend/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── api/
│   │   └── v1/
│   ├── tests/
│   └── seed.py
│
├── alembic/
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md