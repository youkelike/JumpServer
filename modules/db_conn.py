from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(settings.DB_CONN,echo=False)

SessionCls = sessionmaker(bind=engine)
session = SessionCls()