from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

database_url = settings.DATABASE_URL

# Supabase pooler works best without SQLAlchemy pooling
if "pooler.supabase.com" in database_url:
    engine = create_engine(
        database_url,
        echo=settings.ENVIRONMENT == "development",
        poolclass=NullPool,
        connect_args={"sslmode": "require"}
    )
else:
    engine = create_engine(
        database_url,
        echo=settings.ENVIRONMENT == "development",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
