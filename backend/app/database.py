from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Float, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class RobotPathLog(Base):
    """Stores robot path positions over time."""
    __tablename__ = "robot_path_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    robot_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    theta: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class BatteryHistory(Base):
    """Stores robot battery level history."""
    __tablename__ = "battery_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    robot_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    battery_level: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class ErrorLog(Base):
    """Stores robot error logs."""
    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    robot_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="ERROR")
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class TelemetryLog(Base):
    """Stores complete robot telemetry snapshots."""
    __tablename__ = "telemetry_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    robot_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    battery_level: Mapped[float] = mapped_column(Float, nullable=True)
    x: Mapped[float] = mapped_column(Float, nullable=True)
    y: Mapped[float] = mapped_column(Float, nullable=True)
    theta: Mapped[float] = mapped_column(Float, nullable=True)
    raw_data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string of full payload
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


# Database engine and session management
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.database_path}",
    echo=settings.database_echo,
    connect_args={
        "timeout": 30.0,  # Increase timeout for locked database (default is 5)
        "check_same_thread": False,  # Allow SQLite to be used across threads
    },
    # Note: SQLite doesn't support pool_size/max_overflow parameters
    # It uses NullPool by default which is appropriate for SQLite
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions in FastAPI endpoints."""
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """Initialize database tables and enable WAL mode for better concurrency."""
    async with engine.begin() as conn:
        # Enable WAL (Write-Ahead Logging) mode for better concurrent writes
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        # Reduce fsync calls for better performance
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL")
        # Set busy timeout at SQLite level (in addition to connection timeout)
        await conn.exec_driver_sql("PRAGMA busy_timeout=30000")

        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
