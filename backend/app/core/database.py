import logging
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

logger = logging.getLogger(__name__)

database_url = settings.DATABASE_URL
url = make_url(database_url)
logger.info(
    "Database URL parsed: %s (user=%s host=%s port=%s db=%s)",
    url.render_as_string(hide_password=True),
    url.username,
    url.host,
    url.port,
    url.database,
)

# Supabase pooler works best without SQLAlchemy pooling
if "pooler.supabase.com" in database_url:
    if url.username == "postgres":
        raise RuntimeError(
            "Supabase pooler requires the pooler username 'postgres.<project-ref>' "
            "(not 'postgres'). Update DATABASE_URL from the Transaction pooler tab."
        )
    engine = create_engine(
        database_url,
        echo=settings.ENVIRONMENT == "development",
        poolclass=NullPool,
        connect_args={
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        pool_pre_ping=True,
        use_native_hstore=False,
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
