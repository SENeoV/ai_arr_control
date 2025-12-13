"""Database session and initialization."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from db.models import Base
from loguru import logger

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL logging in debug mode
    pool_pre_ping=True,  # Test connections before using them
)

# Create async session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize the database by creating all tables.
    
    This should be called during application startup. It creates all tables
    defined in the models if they don't already exist.
    """
    logger.info("Initializing database")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialization successful")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close the database engine and all connections.
    
    This should be called during application shutdown.
    """
    logger.info("Closing database connections")
    await engine.dispose()
