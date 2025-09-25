from sqlalchemy import create_engine, Column, Integer, String, Double, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator, Optional
import os
Base = declarative_base()

def get_compose_postgres_url(
        *,
        host: Optional[str] = None,
        port: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        db: Optional[str] = None,
) -> str:
        """Build a Postgres connection string using docker-compose defaults with env overrides.

        Defaults match docker-compose service localize_postgres_central:
            host=localhost, port=5432, user=admin, password=password123, db=localize_central_db
        """
        host = host or os.getenv("PG_HOST", "localhost")
        port = port or os.getenv("PG_PORT", "5432")
        user = user or os.getenv("PG_USER", "admin")
        password = password or os.getenv("PG_PASSWORD", "password123")
        db = db or os.getenv("PG_DB", "localize_central_db")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


# --- Database session setup (compose-aware with local fallback) ---
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or get_compose_postgres_url()
engine = create_engine(DATABASE_URL, future=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Ensure tables exist for local/dev usage
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    # In some deployment contexts, migrations manage tables; ignore here
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Convenience exports for apps that want direct access
def get_engine():
    return engine


def get_session_factory():
    return SessionLocal

class Citizen(Base):
    __tablename__ = 'citizens'
    citizen_id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(String, unique=True, index=True)
    gov_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    
class Business(Base):
    __tablename__ = 'businesses'
    business_id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(String, unique=True, index=True)
    business_name = Column(String, nullable=False)
    business_reg_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    province = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address1 = Column(String, nullable=False)
        
    longitude = Column(Double, nullable=True)
    latitude = Column(Double, nullable=True)
    
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    bussiness_type = Column(String, nullable=True)  # New field for business type

class Manufacturer(Base):
    __tablename__ = 'manufacturers'
    manufacturer_id = Column(Integer, autoincrement=True, primary_key=True)
    uuid = Column(String, unique=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    business_name = Column(String, nullable=False)
    business_reg_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    province = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address1 = Column(String, nullable=False)
    
    longitude = Column(Double, nullable=True)
    latitude = Column(Double, nullable=True)    
    
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    
if __name__ == "__main__":
    print(f"Using DATABASE_URL: {DATABASE_URL}")
    print("Creating tables if not exist...")
    engine.echo = True
    Base.metadata.create_all(bind=engine)
    engine.echo = False
    print("Done.")