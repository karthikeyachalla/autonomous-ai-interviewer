from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings
from backend.database.models import Base
import os


DATABASE_URL = settings.DATABASE_URL


def init_db():
    dirpath = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    print("DB initialized:", DATABASE_URL)


def get_engine():
    return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def get_session():
    engine = get_engine()
    return sessionmaker(bind=engine)()
