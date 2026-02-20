from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Website(Base):
    __tablename__ = "websites"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    gsc_property = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    keywords = relationship("Keyword", back_populates="website", cascade="all, delete-orphan")
    audits = relationship("Audit", back_populates="website", cascade="all, delete-orphan")
    gsc_data = relationship("GSCData", back_populates="website", cascade="all, delete-orphan")

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    keyword = Column(String(500), nullable=False)
    volume = Column(Integer, nullable=True)
    difficulty = Column(Float, nullable=True)
    current_rank = Column(Integer, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    
    website = relationship("Website", back_populates="keywords")

class Audit(Base):
    __tablename__ = "audits"
    
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    audit_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    results_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    website = relationship("Website", back_populates="audits")

class GSCData(Base):
    __tablename__ = "gsc_data"
    
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    url = Column(String(1000), nullable=False)
    clicks = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    position = Column(Float, nullable=True)
    date = Column(DateTime, nullable=False)
    
    website = relationship("Website", back_populates="gsc_data")

# Database setup
def get_engine():
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/seo_executive.db")
    return create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})

def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()
