"""
Database configuration and connection management
Enterprise-level database setup with connection pooling
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from contextlib import contextmanager
import logging
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/academic_advisor"
)

# Engine configuration with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)

# Session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
)

Base = declarative_base()

# Database dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Database session generator for dependency injection
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

# Connection event listeners
@event.listens_for(pool.Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Set connection pragmas for better performance
    """
    if 'sqlite' in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """
    Log new database connections
    """
    logger.info(f"New database connection established: {connection_record.info}")

# Health check
def check_database_health() -> bool:
    """
    Check if database is accessible
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

# Initialize database
def init_db():
    """
    Initialize database tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise

# Cleanup
def dispose_db():
    """
    Dispose database connections
    """
    SessionLocal.remove()
    engine.dispose()
    logger.info("Database connections disposed")