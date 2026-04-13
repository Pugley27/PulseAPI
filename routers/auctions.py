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

@router.post("/add-auction")
def add_auction(auction: schemas.AuctionCreate, db: Session = Depends(get_db), _ = Depends(verify_key)):  
    # First we need to get the item name for the response, and make sure it is a valid item ID
    item_name_result = db.execute(text("SELECT name FROM auction_items WHERE id = :item_id"), {"item_id": auction.item_id})
    item_result = item_name_result.fetchone()
    print(f"Querying for item ID: {auction.item_id}. Result: {item_result}")
    if not item_result:
        raise HTTPException(status_code=400, detail="Invalid item ID. Please check the item ID and try again.")
    item_name = item_result[0]
    print(f"Item name for item ID {auction.item_id} is {item_name}")
    # Insert the auction into the database
    stmt = text("INSERT INTO auctions (name, description, item_id) VALUES (:name, :description, :item_id) returning id")
    result = db.execute(stmt, {"name": auction.name, "description": auction.description, "item_id": auction.item_id})
    return_result = result.fetchone();
    if not return_result:
        raise HTTPException(status_code=400, detail="Failed to create auction. Please check the item ID and try again.")
    id = return_result[0]

    db.commit()
    return {"status": "created", "auction_id": id, "item_name": item_name}