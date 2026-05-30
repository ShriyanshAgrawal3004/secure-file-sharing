from datetime import datetime
import os

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'vault.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FileIndex(Base):
    __tablename__ = "file_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, unique=True, nullable=False, index=True)
    owner_wallet = Column(String, ForeignKey("users.wallet_address"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    algorithm = Column(String, nullable=False)
    ipfs_hash = Column(String, nullable=True)
    tx_hash = Column(String, nullable=True)
    sensitivity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", primaryjoin="FileIndex.owner_wallet == User.wallet_address")


class AccessRequest(Base):
    __tablename__ = "access_requests"
    __table_args__ = (UniqueConstraint("file_id", "requester_address", name="uq_file_requester"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, nullable=False, index=True)
    requester_address = Column(String, nullable=False, index=True)
    status = Column(String, default="PENDING", nullable=False, index=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    return SessionLocal()
