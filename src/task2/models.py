from sqlalchemy import Integer, String, Float, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SpimexTradingResults(Base):
    __tablename__ = 'spimex_trading_results'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    exchange_product_id: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange_product_name: Mapped[str] = mapped_column(String(500), nullable=False)

    oil_id: Mapped[str] = mapped_column(String(4), nullable=False)
    delivery_basis_id: Mapped[str] = mapped_column(String(3), nullable=False)
    delivery_type_id: Mapped[str] = mapped_column(String(1), nullable=False)

    delivery_basis_name: Mapped[str] = mapped_column(String(500), nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)

    created_on: Mapped[DateTime] = mapped_column(server_default=func.now())
    updated_on: Mapped[DateTime] = mapped_column(server_default=func.now(), onupdate=func.now())