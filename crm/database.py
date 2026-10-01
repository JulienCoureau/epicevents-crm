from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crm.config import database_url

engine = create_engine(database_url())
SessionLocal = sessionmaker(bind=engine)
