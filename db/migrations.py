"""Database migration utilities for production deployments.

Supports schema versioning and migration tracking for safe upgrades.
"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime
from datetime import datetime, timezone
from loguru import logger

# Get current UTC time in a timezone-aware manner
def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for migration models."""
    pass


class SchemaMigration(Base):
    """Track applied schema migrations."""
    
    __tablename__ = "schema_migrations"
    
    # Unique migration version
    version: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # When this migration was applied
    applied_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Description of what this migration does
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Migration {self.version} applied at {self.applied_at}>"


class MigrationManager:
    """Manages database migrations for version upgrades."""
    
    def __init__(self, engine: any) -> None:
        """Initialize migration manager.
        
        Args:
            engine: SQLAlchemy async engine instance
        """
        self.engine = engine
        self.applied_migrations: set = set()
    
    async def initialize_migrations_table(self) -> None:
        """Create migrations tracking table if it doesn't exist."""
        logger.info("Initializing schema_migrations table")
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(SchemaMigration.__table__.create, checkfirst=True)
            logger.info("Migrations table ready")
        except Exception as e:
            logger.error(f"Failed to initialize migrations table: {e}")
            raise
    
    async def get_applied_migrations(self) -> set:
        """Get set of migration versions that have been applied."""
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        
        logger.debug("Checking applied migrations")
        try:
            async with AsyncSession(self.engine) as session:
                result = await session.execute(select(SchemaMigration.version))
                return set(result.scalars().all())
        except Exception as e:
            logger.warning(f"Could not fetch applied migrations: {e}")
            return set()
    
    async def record_migration(self, version: str, description: str = "") -> None:
        """Record that a migration has been applied.
        
        Args:
            version: Migration version identifier
            description: Human-readable description
        """
        from sqlalchemy.ext.asyncio import AsyncSession
        
        logger.info(f"Recording migration: {version}")
        try:
            async with AsyncSession(self.engine) as session:
                migration = SchemaMigration(
                    version=version,
                    description=description,
                    applied_at=utc_now()
                )
                session.add(migration)
                await session.commit()
            logger.info(f"Migration {version} recorded")
        except Exception as e:
            logger.error(f"Failed to record migration {version}: {e}")
            raise
