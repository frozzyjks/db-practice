from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base

class Genre(Base):
    __tablename__ = 'genre'

    genre_id = Column(Integer, primary_key=True, autoincrement=True)
    name_genre = Column(String(100), nullable=False)

    books = relationship('Book', back_populates='genre')


class Author(Base):
    __tablename__ = 'author'

    author_id = Column(Integer, primary_key=True, autoincrement=True)
    name_author = Column(String(150), nullable=False)

    books = relationship('Book', back_populates='author')


class Book(Base):
    __tablename__ = 'book'

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    amount = Column(Integer, nullable=False)

    author_id = Column(Integer, ForeignKey('author.author_id'), nullable=False)
    genre_id = Column(Integer, ForeignKey('genre.genre_id'), nullable=False)

    author = relationship('Author', back_populates='books')
    genre = relationship('Genre', back_populates='books')
    buy_books = relationship('BuyBook', back_populates='book')


class City(Base):
    __tablename__ = 'city'

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    name_city = Column(String(100), nullable=False)
    days_delivery = Column(Integer, nullable=False)

    clients = relationship('Client', back_populates='city')


class Client(Base):
    __tablename__ = 'client'

    client_id = Column(Integer, primary_key=True, autoincrement=True)
    name_client = Column(String(150), nullable=False)
    email = Column(String(200), nullable=False)

    city_id = Column(Integer, ForeignKey('city.city_id'), nullable=False)

    city = relationship('City', back_populates='clients')
    buys = relationship('Buy', back_populates='client')


class Buy(Base):
    __tablename__ = 'buy'

    buy_id = Column(Integer, primary_key=True, autoincrement=True)
    buy_description = Column(String(500), nullable=True)

    client_id = Column(Integer, ForeignKey('client.client_id'), nullable=False)

    client = relationship('Client', back_populates='buys')
    buy_books = relationship('BuyBook', back_populates='buy')
    buy_steps = relationship('BuyStep', back_populates='buy')


class BuyBook(Base):
    __tablename__ = 'buy_book'

    buy_book_id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer, nullable=False)

    buy_id = Column(Integer, ForeignKey('buy.buy_id'), nullable=False)
    book_id = Column(Integer, ForeignKey('book.book_id'), nullable=False)

    buy = relationship('Buy', back_populates='buy_books')
    book = relationship('Book', back_populates='buy_books')


class Step(Base):
    __tablename__ = 'step'

    step_id = Column(Integer, primary_key=True, autoincrement=True)
    name_step = Column(String(100), nullable=False)

    buy_steps = relationship('BuyStep', back_populates='step')


class BuyStep(Base):
    __tablename__ = 'buy_step'

    buy_step_id = Column(Integer, primary_key=True, autoincrement=True)
    date_step_beg = Column(Date, nullable=True)
    date_step_end = Column(Date, nullable=True)

    buy_id = Column(Integer, ForeignKey('buy.buy_id'), nullable=False)
    step_id = Column(Integer, ForeignKey('step.step_id'), nullable=False)

    buy = relationship('Buy', back_populates='buy_steps')
    step = relationship('Step', back_populates='buy_steps')