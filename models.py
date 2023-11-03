from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
import datetime


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    admin = Column(Boolean)
    username = Column(String)
    hashed_password = Column(String)


class Todos(Base):
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id"), default=0)
    title = Column(String)
    description = Column(String)
    is_important = Column(Boolean)
    is_completed = Column(Boolean, default=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)


