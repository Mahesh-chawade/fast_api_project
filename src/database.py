import uuid
import datetime
from sqlalchemy import create_engine, Column, String, Float, Date, Table, MetaData
from sqlalchemy.orm import sessionmaker, Session, declarative_base


DATABASE_URL = "sqlite:///databases/transactions_info.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



class DatabaseManager:
    @staticmethod
    def get_user_transactions_table(user_name: str):
        table_name = f"{user_name}_transactions"

        return Table(
            table_name,
            metadata,
            Column("reference_no", String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())),
            Column("date", Date, index=True),
            Column("details", String, index=True, default="REF418873"),
            Column("debit", Float, default=0.0),
            Column("credit", Float, default=0.0),
            extend_existing=True,
        )

    @staticmethod
    def ensure_table_exists(user_table):
        """Ensures the user's transaction table exists."""
        metadata.create_all(engine)
