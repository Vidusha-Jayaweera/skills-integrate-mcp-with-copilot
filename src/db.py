from sqlmodel import SQLModel, create_engine, Session
import os

# Allow overriding DB via DATABASE_URL env var (e.g., postgres://...)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# echo SQL for debugging when needed
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
