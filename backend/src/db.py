import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
engine=create_engine(os.environ['DATABASE_URL'],pool_pre_ping=True,isolation_level='READ COMMITTED')
Session=sessionmaker(engine,expire_on_commit=False)
class Base(DeclarativeBase):pass
def session():
    with Session() as s:yield s
