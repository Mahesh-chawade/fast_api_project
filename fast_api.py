from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
import uuid
import datetime
from src.auth import router as auth_router, get_current_user
from src.database import DatabaseManager, get_db, engine, metadata, Table

app = FastAPI()
app.include_router(auth_router)


class BankTransactionCreate(BaseModel):
    date: str
    details: str = "None"
    debit: float = 0.0
    credit: float = 0.0

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            return datetime.datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date format must be YYYY-MM-DD")



## 🟢 Create Transaction
@app.post("/transactions/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: BankTransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_table = DatabaseManager.get_user_transactions_table(current_user.username)
    DatabaseManager.ensure_table_exists(user_table)

    reference_no = str(uuid.uuid4())  # Generate unique reference number

    insert_stmt = user_table.insert().values(
        reference_no=reference_no,
        date=transaction.date,
        details=transaction.details,
        debit=transaction.debit,
        credit=transaction.credit,
    )
    db.execute(insert_stmt)
    db.commit()

    return {"reference_no" : f"{reference_no}"}


## 🔵 Fetch Transaction by Reference No
@app.get("/transactions/{reference_no}")
async def read_transaction(
    reference_no: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    table_name = f"{current_user.username}_transactions"

    try:
        user_table = Table(table_name, metadata, autoload_with=engine)
    except Exception:
        raise HTTPException(status_code=404, detail=f"User table '{table_name}' does not exist")

    session = db
    select_stmt = user_table.select().where(user_table.c.reference_no == reference_no)
    transaction = session.execute(select_stmt).fetchone()

    if not transaction:
        raise HTTPException(status_code=404, detail=f"Transaction with reference {reference_no} not found")

    return dict(zip(transaction._fields, transaction))


## 🟡 Update Transaction (PUT)
@app.put("/transactions/{reference_no}")
async def update_transaction(
    reference_no: str,
    transaction: BankTransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    table_name = f"{current_user.username}_transactions"

    try:
        user_table = Table(table_name, metadata, autoload_with=engine)
    except Exception:
        raise HTTPException(status_code=404, detail=f"User table '{table_name}' does not exist")

    session = db

    # Check if the transaction exists
    select_stmt = user_table.select().where(user_table.c.reference_no == reference_no)
    existing_transaction = session.execute(select_stmt).fetchone()

    if not existing_transaction:
        raise HTTPException(status_code=404, detail=f"Transaction with reference {reference_no} not found")

    # Update the transaction
    update_stmt = user_table.update().where(user_table.c.reference_no == reference_no).values(
        date=transaction.date,
        details=transaction.details,
        debit=transaction.debit,
        credit=transaction.credit
    )

    session.execute(update_stmt)
    session.commit()

    return {"message": f"Transaction {reference_no} updated successfully"}


## 🔴 Delete Transaction (DELETE)
@app.delete("/transactions/{reference_no}")
async def delete_transaction(
    reference_no: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    table_name = f"{current_user.username}_transactions"

    try:
        user_table = Table(table_name, metadata, autoload_with=engine)
    except Exception:
        raise HTTPException(status_code=404, detail=f"User table '{table_name}' does not exist")

    session = db

    # Check if the transaction exists
    select_stmt = user_table.select().where(user_table.c.reference_no == reference_no)
    existing_transaction = session.execute(select_stmt).fetchone()

    if not existing_transaction:
        raise HTTPException(status_code=404, detail=f"Transaction with reference {reference_no} not found")

    # Delete the transaction
    delete_stmt = user_table.delete().where(user_table.c.reference_no == reference_no)
    session.execute(delete_stmt)
    session.commit()

    return {"message": f"Transaction {reference_no} deleted successfully"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
