from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Person(Base):
    __tablename__ = 'people'
    email = Column(Text, unique=True)
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    phone = Column(Text, unique=True)
