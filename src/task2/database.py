from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from src.task2.config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()

# retry connection (FIX для docker startup race condition)
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        connection = engine.connect()
        connection.close()
        break
    except Exception as e:
        print(f"DB not ready, retry {i+1}/10")
        time.sleep(2)
else:
    raise Exception("Database is not available")

Session = sessionmaker(bind=engine)