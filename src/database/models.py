from sqlalchemy import func, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.sqltypes import Date


Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    lastname = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(50))
    birthday = Column(Date)
    note = Column(String(250))
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'),
                     default=None)
    user = relationship('User', backref="contacts")
    __table_args__ = (UniqueConstraint( 'name', 'lastname', name='fullname_uc'),)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
