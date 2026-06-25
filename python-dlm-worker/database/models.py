import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import create_engine, String, Numeric, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.sql import func
from config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

Base = declarative_base()


class MainUser(Base):
    """User model - main schema for Java service"""
    __tablename__ = "users"
    __table_args__ = {"schema": "main"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    terms_accepted: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )


class MainVehicle(Base):
    """Vehicle model - main schema for Java service"""
    __tablename__ = "vehicles"
    __table_args__ = {"schema": "main"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="available")
    current_location: Mapped[Optional[dict]] = mapped_column(JSON)
    fuel_level: Mapped[Optional[float]] = mapped_column(default=100.0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )


class MainRide(Base):
    """Ride model - main schema for Java service"""
    __tablename__ = "rides"
    __table_args__ = {"schema": "main"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    start_location: Mapped[dict] = mapped_column(JSON, nullable=False)
    end_location: Mapped[Optional[dict]] = mapped_column(JSON)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MainTelemetry(Base):
    """Telemetry model - main schema for Java service"""
    __tablename__ = "telemetry"
    __table_args__ = {"schema": "main"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    ride_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    vehicle_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MainPayment(Base):
    """Payment model - main schema for Java service"""
    __tablename__ = "payments"
    __table_args__ = {"schema": "main"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True)
    ride_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))


class ArchiveRide(Base):
    """Archived ride model - archive schema for DLM worker"""
    __tablename__ = "rides"
    __table_args__ = {"schema": "archive"}

    id: Mapped[int] = mapped_column(Numeric, primary_key=True)
    user_id: Mapped[int] = mapped_column(Numeric, nullable=False)
    car_id: Mapped[int] = mapped_column(Numeric, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    end_reason: Mapped[Optional[str]] = mapped_column(String(50))
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    archived_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ArchivePayment(Base):
    """Archived payment model - archive schema for DLM worker"""
    __tablename__ = "payments_archive"
    __table_args__ = {"schema": "archive"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ride_id: Mapped[int] = mapped_column(Numeric, nullable=False)
    user_id: Mapped[int] = mapped_column(Numeric, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    archived_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
