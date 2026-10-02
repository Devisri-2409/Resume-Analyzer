import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

# For Neon Serverless Postgres with PgBouncer connection pooler:
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    connect_args={
        "connect_timeout": 15,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    retries = 3
    db = None
    while retries > 0:
        try:
            db = SessionLocal()
            # Verify connection is live
            db.connection()
            break
        except Exception as e:
            retries -= 1
            if db:
                try:
                    db.close()
                except Exception:
                    pass
            if retries == 0:
                raise e
            time.sleep(0.5)

    try:
        yield db
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass
            pass