from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

# DB Vars from settings
settings = get_settings()

db_user = settings.POSTGRES_USER
db_password = settings.POSTGRES_PASSWORD
db_name = settings.POSTGRES_DB
db_host = settings.POSTGRES_HOST
db_port = settings.POSTGRES_PORT

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
# Create the SQLAlchemy engine and session factory
engine = create_engine(
	str(DATABASE_URL), 
	pool_pre_ping=True,
    pool_size=5,
	pool_recycle=3600,
    echo=False
)
DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)

def get_dbsession():
    """Dependency for getting DB sessions."""
    db = DBSession()
    try:
       yield db
    finally:
        db.close()