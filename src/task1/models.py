from sqlalchemy import Integer, String, Numeric, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Genre(Base):
    __tablename__ = 'genre'

    genre_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_genre: Mapped[str] = mapped_column(String(100), nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="genre")


class Author(Base):
    __tablename__ = 'author'

    author_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_author: Mapped[str] = mapped_column(String(150), nullable=False)

    books: Mapped[list["Book"]] = relationship(back_populates="author")


class Book(Base):
    __tablename__ = 'book'

    book_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    author_id: Mapped[int] = mapped_column(ForeignKey('author.author_id'), nullable=False)
    genre_id: Mapped[int] = mapped_column(ForeignKey('genre.genre_id'), nullable=False)

    author: Mapped["Author"] = relationship(back_populates="books")
    genre: Mapped["Genre"] = relationship(back_populates="books")
    buy_books: Mapped[list["BuyBook"]] = relationship(back_populates="book")


class City(Base):
    __tablename__ = 'city'

    city_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_city: Mapped[str] = mapped_column(String(100), nullable=False)
    days_delivery: Mapped[int] = mapped_column(Integer, nullable=False)

    clients: Mapped[list["Client"]] = relationship(back_populates="city")


class Client(Base):
    __tablename__ = 'client'

    client_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_client: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)

    city_id: Mapped[int] = mapped_column(ForeignKey('city.city_id'), nullable=False)

    city: Mapped["City"] = relationship(back_populates="clients")
    buys: Mapped[list["Buy"]] = relationship(back_populates="client")


class Buy(Base):
    __tablename__ = 'buy'

    buy_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buy_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    client_id: Mapped[int] = mapped_column(ForeignKey('client.client_id'), nullable=False)

    client: Mapped["Client"] = relationship(back_populates="buys")
    buy_books: Mapped[list["BuyBook"]] = relationship(back_populates="buy")
    buy_steps: Mapped[list["BuyStep"]] = relationship(back_populates="buy")


class BuyBook(Base):
    __tablename__ = 'buy_book'

    buy_book_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    buy_id: Mapped[int] = mapped_column(ForeignKey('buy.buy_id'), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey('book.book_id'), nullable=False)

    buy: Mapped["Buy"] = relationship(back_populates="buy_books")
    book: Mapped["Book"] = relationship(back_populates="buy_books")


class Step(Base):
    __tablename__ = 'step'

    step_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_step: Mapped[str] = mapped_column(String(100), nullable=False)

    buy_steps: Mapped[list["BuyStep"]] = relationship(back_populates="step")


class BuyStep(Base):
    __tablename__ = 'buy_step'

    buy_step_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date_step_beg: Mapped[Date | None] = mapped_column(Date, nullable=True)
    date_step_end: Mapped[Date | None] = mapped_column(Date, nullable=True)

    buy_id: Mapped[int] = mapped_column(ForeignKey('buy.buy_id'), nullable=False)
    step_id: Mapped[int] = mapped_column(ForeignKey('step.step_id'), nullable=False)

    buy: Mapped["Buy"] = relationship(back_populates="buy_steps")
    step: Mapped["Step"] = relationship(back_populates="buy_steps")