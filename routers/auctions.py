# This file handles the routing code for tracking member currency.
from sqlalchemy.exc import  IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, verify_key
import schemas
from fastapi import HTTPException, Depends
import datetime

router = APIRouter(
    prefix="/auctions",
    tags=["Auctions"]
)

@router.post("/add-item")
def add_item(item: schemas.ItemCreate, db: Session = Depends(get_db), _ = Depends(verify_key)):  
    # Insert the item into the database
    stmt = text("INSERT INTO auction_items (name, description) VALUES (:name, :description) returning id")
    result = db.execute(stmt, {"name": item.name, "description": item.description})
    id = result.fetchone()[0]
    db.commit()
    return {"status": "created", "item_id": id}
