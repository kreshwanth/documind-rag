import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("documind.database")

Base = declarative_base()

def create_configured_engine(db_url: str):
    is_sqlite = db_url.startswith("sqlite")
    kwargs = {
        "pool_pre_ping": True,
        "connect_args": {"check_same_thread": False} if is_sqlite else {"connect_timeout": 3}
    }
    if not is_sqlite:
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
    return create_engine(db_url, **kwargs)

# Try initial connection; if PostgreSQL is offline, gracefully use local SQLite
active_db_url = settings.DATABASE_URL
try:
    if not active_db_url.startswith("sqlite"):
        test_engine = create_configured_engine(active_db_url)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        engine = test_engine
        logger.info(f"Connected to PostgreSQL database: {active_db_url}")
    else:
        engine = create_configured_engine(active_db_url)
except Exception as e:
    fallback_sqlite_url = "sqlite:///./documind.db"
    logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to local SQLite database: {fallback_sqlite_url}")
    active_db_url = fallback_sqlite_url
    settings.DATABASE_URL = fallback_sqlite_url
    engine = create_configured_engine(fallback_sqlite_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Ensure vector extension is available in PostgreSQL and all tables exist."""
    global engine, active_db_url
    
    # Import all models to ensure metadata registration
    import app.models.user
    import app.models.document
    import app.models.chunk
    import app.models.conversation

    if not active_db_url.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("Vector extension ensured in PostgreSQL.")
        except Exception as e:
            logger.warning(f"PostgreSQL vector setup warning: {e}")
            
    # Create all tables if they do not already exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All DocuMind database tables created and verified.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)

def get_db():
    """Dependency for obtaining database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

