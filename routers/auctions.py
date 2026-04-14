# This file handles the routing code for tracking member currency.
from sqlalchemy.exc import  IntegrityError
from sqlalchemy import null, text
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

@router.get("/items")
def get_items(db: Session = Depends(get_db), _ = Depends(verify_key)):
    result = db.execute(text("SELECT id, name, description FROM auction_items"))
    items = [{"id": row[0], "name": row[1], "description": row[2]} for row in result.fetchall()]
    return {"items": items}

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

    # CHECK: Does an auction for this item_id already exist?
    # We check if there's any record in the 'auctions' table with this item_id
    existing_auction = db.execute(
        text("SELECT id FROM auctions WHERE item_id = :item_id"), 
        {"item_id": auction.item_id}
    ).fetchone()

    if existing_auction:
        raise HTTPException(
            status_code=400, 
            detail=f"Item '{item_name}' (ID: {auction.item_id}) is already listed in an active auction."
        )
    
    # Insert the auction into the database
    stmt = text("INSERT INTO auctions (name, description, item_id) VALUES (:name, :description, :item_id) returning id")
    result = db.execute(stmt, {"name": auction.name, "description": auction.description, "item_id": auction.item_id})
    return_result = result.fetchone();
    if not return_result:
        raise HTTPException(status_code=400, detail="Failed to create auction. Please check the item ID and try again.")
    id = return_result[0]

    db.commit()
    return {"status": "created", "auction_id": id, "item_name": item_name}

@router.get("/active")
def get_active_auctions(db: Session = Depends(get_db), _ = Depends(verify_key)):
    result = db.execute(text("SELECT auctions.id, auctions.name, auctions.description, auctions.end_time, auction_items.name as item_name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.active = true"))
    auctions = [{"id": row[0], "name": row[1], "description": row[2], "end_time": row[3], "item_name": row[4]} for row in result.fetchall()]
    return {"auctions": auctions}

@router.get("/unscheduled")
def get_unscheduled_auctions(db: Session = Depends(get_db), _ = Depends(verify_key)):
    result = db.execute(text("SELECT auctions.id, auctions.name, auctions.description, auction_items.name as item_name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.active = false or auctions.active is null"))
    auctions = [{"id": row[0], "name": row[1], "description": row[2], "item_name": row[3]} for row in result.fetchall()]
    return {"auctions": auctions}

@router.post("/start-auction")
def start_auction(request: schemas.StartAuctionRequest, db: Session = Depends(get_db), _ = Depends(verify_key)):
    # First we need to check if the auction ID is valid and get the item name for the response
    auction_result = db.execute(text("SELECT auctions.name, auction_items.name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.id = :auction_id"), {"auction_id": request.auction_id})
    auction_row = auction_result.fetchone()
    print(f"Querying for auction ID: {request.auction_id}. Result: {auction_row}")
    if not auction_row:
        raise HTTPException(status_code=400, detail="Invalid auction ID. Please check the auction ID and try again.")
    auction_name = auction_row[0]
    item_name = auction_row[1]
    print(f"Auction name for auction ID {request.auction_id} is {auction_name} and item name is {item_name}")

    # Then we update the auction to set it as active and set the end time based on the duration in DD/MM/YYYY HH:MM format
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=request.duration_minutes)
    result = db.execute(text("UPDATE auctions SET active = true, end_time = :end_time WHERE id = :auction_id returning id"), {"end_time": end_time, "auction_id": request.auction_id})
    updated_auction = result.fetchone()
    if not updated_auction:
        raise HTTPException(status_code=400, detail="Failed to start the auction. Please check the auction ID and try again.")
    
    db.commit()
    return {"status": "started", "auction_id": request.auction_id, "item_name": item_name, "end_time": end_time.isoformat()}

@router.post("/place-bid")
def place_bid(request: schemas.BidRequest, db: Session = Depends(get_db), _ = Depends(verify_key)):
    # First we need to check if the auction ID is valid and get the item name for the response
    auction_result = db.execute(text("SELECT auctions.name, auction_items.name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.id = :auction_id AND auctions.active = true"), {"auction_id": request.auction_id})
    auction_row = auction_result.fetchone()
    print(f"Querying for active auction ID: {request.auction_id}. Result: {auction_row}")
    if not auction_row:
        raise HTTPException(status_code=400, detail="Invalid or inactive auction ID. Please check the auction ID and try again.")
    auction_name = auction_row[0]
    item_name = auction_row[1]
    print(f"Auction name for auction ID {request.auction_id} is {auction_name} and item name is {item_name}")

    # Then we need to check if the user has enough balance to place the bid
    query = text('SELECT cruor_amount FROM "lockBox" WHERE member_id = :user_id') # TODO fix lockbox table name so it is not case sensitive and doesn't require quotes
    balance_result = db.execute(query, {"user_id": request.user_id})    
    balance_row = balance_result.fetchone()
    balance = balance_row[0] if balance_row else 0
    print(f"User ID {request.user_id} has a balance of {balance} Cruor")

    if request.amount > balance:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. You have {balance} Cruor but your bid is for {request.amount} Cruor.")

    # If they have enough balance, we insert or update their bid for this auction
    stmt = text("""
        INSERT INTO bids (auction_id, user_id, amount) VALUES (:auction_id, :user_id, :amount)
        ON CONFLICT (auction_id, user_id) DO UPDATE SET amount = EXCLUDED.amount
        RETURNING amount
    """)
    result = db.execute(stmt, {"auction_id": request.auction_id, "user_id": request.user_id, "amount": request.amount})
    updated_bid = result.fetchone()
    print(f"Placing bid for user ID {request.user_id} on auction ID {request.auction_id} with amount {request.amount}. Result: {updated_bid}")
    if not updated_bid:
        raise HTTPException(status_code=400, detail="Failed to place bid. Please check the auction ID and try again.")
    
    db.commit()
    return {"status": "success", "auction_id": request.auction_id, "item_name": item_name, "bid_amount": updated_bid[0]}
