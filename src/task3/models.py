from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from src.task3.database import Base


class SpimexTradingResults(Base):
    __tablename__ = 'spimex_trading_results'

    id = Column(Integer, primary_key=True)
    exchange_product_id = Column(String(20))
    exchange_product_name = Column(String(500))
    oil_id = Column(String(4))
    delivery_basis_id = Column(String(3))
    delivery_type_id = Column(String(1))
    delivery_basis_name = Column(String(500))
    volume = Column(Float)
    total = Column(Float)
    count = Column(Integer)
    date = Column(Date)
    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, server_default=func.now(), onupdate=func.now())