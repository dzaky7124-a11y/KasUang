from sqlmodel import SQLModel, create_engine, Session
from app.config import DATABASE_URL

# Configure connect_args for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

def init_db():
    from app import models  # ensure models are imported before creating tables
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
