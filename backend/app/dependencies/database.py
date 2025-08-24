from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

# Create the SQLAlchemy engine and session factory
settings = get_settings()
engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

def get_db():
    """Dependency for getting DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()