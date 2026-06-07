from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

# DB Vars from settings
settings = get_settings()

db_user = settings.POSTGRES_USER
db_password = settings.POSTGRES_PASSWORD
db_name = settings.POSTGRES_DB
db_host = settings.POSTGRES_HOST
db_port = settings.POSTGRES_PORT

# URL.create() stores the password in a structured object; repr() masks it as
# "***" so it can never appear in logs or exception messages.
DATABASE_URL = URL.create(
    drivername="postgresql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_name,
)
# Create the SQLAlchemy engine and session factory
engine = create_engine(
    DATABASE_URL,
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