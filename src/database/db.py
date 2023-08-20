from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from src.conf.config import settings


SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://" \
    + f"{settings.postgresql_user}:{settings.postgresql_password}" \
    + f"@{settings.postgresql_host}:{settings.postgresql_port}" \
    + f"/{settings.postgresql_db}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
