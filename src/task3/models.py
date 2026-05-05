from datetime import date, datetime
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.task3.database import Base


class SpimexTradingResults(Base):
    __tablename__ = "spimex_trading_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_product_id: Mapped[str] = mapped_column(String(20))
    exchange_product_name: Mapped[str] = mapped_column(String(500))
    oil_id: Mapped[str] = mapped_column(String(4))
    delivery_basis_id: Mapped[str] = mapped_column(String(3))
    delivery_type_id: Mapped[str] = mapped_column(String(1))
    delivery_basis_name: Mapped[str] = mapped_column(String(500))
    volume: Mapped[float] = mapped_column()
    total: Mapped[float] = mapped_column()
    count: Mapped[int] = mapped_column()
    date: Mapped[date] = mapped_column()
    created_on: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_on: Mapped[Optional[datetime]] = mapped_column(server_default=func.now(), onupdate=func.now())