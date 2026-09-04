from sqlalchemy import text

from app.db.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print(result.fetchone())

    print("Database connection successful!")

except Exception as e:
    print("Database connection failed!")
    print(e)