from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from database import Base


class SpimexTradingResults(Base):
    __tablename__ = 'spimex_trading_results'

    id = Column(Integer, primary_key=True, autoincrement=True)

    exchange_product_id = Column(String(20), nullable=False)
    exchange_product_name = Column(String(500), nullable=False)

    oil_id = Column(String(4), nullable=False)
    delivery_basis_id = Column(String(3), nullable=False)
    delivery_type_id = Column(String(1), nullable=False)

    delivery_basis_name = Column(String(500), nullable=False)
    volume = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    count = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, server_default=func.now(), onupdate=func.now())