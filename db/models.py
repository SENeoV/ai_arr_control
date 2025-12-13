from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean
from datetime import datetime

class Base(DeclarativeBase):
    pass

class IndexerHealth(Base):
    __tablename__ = "indexer_health"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service: Mapped[str] = mapped_column(String(32))
    indexer_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    success: Mapped[bool] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
