"""Database models for storing indexer health check history and audit trail."""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Index
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class IndexerHealth(Base):
    """Record of an indexer health check result.
    
    Stores historical data about indexer test results for auditing, trending,
    and debugging purposes. Can be queried to understand indexer reliability
    over time.
    """
    __tablename__ = "indexer_health"
    
    # Unique identifier for this record
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Service name (e.g., "radarr", "sonarr")
    service: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # Indexer ID within the service
    indexer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Human-readable indexer name
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # Whether the health check passed
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # Error message if check failed (null if successful)
    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Timestamp of when this check was performed
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Index for faster queries by service and timestamp
    __table_args__ = (
        Index("idx_service_timestamp", "service", "timestamp"),
        Index("idx_indexer_id", "indexer_id"),
    )
    
    def __repr__(self) -> str:
        status = "OK" if self.success else f"FAIL: {self.error[:30]}"
        return f"<IndexerHealth {self.service}/{self.name} {status}>"
