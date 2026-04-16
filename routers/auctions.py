# This file handles the routing code for tracking member currency.
from sqlalchemy.exc import  IntegrityError
from sqlalchemy import null, text, func
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
    stmt = text("INSERT INTO auction_items (name, description, status, auction_id, member_id, holder_id) VALUES (:name, :description, :status, :auction_id, :member_id, :holder_id) returning id")
    result = db.execute(stmt, {"name": item.name, "description": item.description, "status": "available", "auction_id": None, "member_id": None, "holder_id": item.holder_id})
    id = result.fetchone()[0]
    db.commit()
    return {"status": "created", "item_id": id}

@router.get("/items")
def get_items(db: Session = Depends(get_db), _ = Depends(verify_key)):
    result = db.execute(text("SELECT id, name, description, status, auction_id, member_id, holder_id FROM auction_items"))
    items = [{"id": row[0], "name": row[1], "description": row[2], "status": row[3], "auction_id": row[4], "member_id": row[5], "holder_id": row[6]} for row in result.fetchall()]
    return {"items": items}

@router.post("/add-auction")
def add_auction(auction: schemas.AuctionCreate, db: Session = Depends(get_db), _ = Depends(verify_key)):  
    # First we need to get the item name for the response, and make sure it is a valid item ID
    item_name_result = db.execute(text("SELECT name FROM auction_items WHERE id = :item_id and status = 'available'"), {"item_id": auction.item_id})
    item_result = item_name_result.fetchone()
    print(f"Querying for item ID: {auction.item_id}. Result: {item_result}")
    if not item_result:
        raise HTTPException(status_code=400, detail="Invalid item ID. Please check the item ID and ensure that the item is available and try again.")
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

    stmt = text("INSERT INTO auctions (name, description, item_id, status) VALUES (:name, :description, :item_id, 'unscheduled') returning id")
    result = db.execute(stmt, {"name": auction.name, "description": auction.description, "item_id": auction.item_id})
    return_result = result.fetchone();
    if not return_result:
        raise HTTPException(status_code=400, detail="Failed to create auction. Please check the item ID and try again.")
    id = return_result[0]
    
    # update the auction item to set the auction_id so we know it is listed in an auction
    db.execute(text("UPDATE auction_items SET auction_id = :auction_id, status = 'listed' WHERE id = :item_id"), {"auction_id": id, "item_id": auction.item_id})

    db.commit()
    return {"status": "created", "auction_id": id, "item_name": item_name}

@router.get("/active")
def get_active_auctions(db: Session = Depends(get_db), _ = Depends(verify_key)):
    result = db.execute(text("SELECT auctions.id, auctions.name, auctions.description, auctions.end_time, auction_items.name as item_name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.status = 'active'"))
    auctions = [{"id": row[0], "name": row[1], "description": row[2], "end_time": row[3], "item_name": row[4]} for row in result.fetchall()]
    return {"auctions": auctions}

@router.get("/unscheduled")
def get_unscheduled_auctions(db: Session = Depends(get_db), _ = Depends(verify_key)):
    result = db.execute(text("SELECT auctions.id, auctions.name, auctions.description, auction_items.name as item_name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.status = 'unscheduled'"))
    auctions = [{"id": row[0], "name": row[1], "description": row[2], "item_name": row[3]} for row in result.fetchall()]
    return {"auctions": auctions}

@router.post("/start-auction")
def start_auction(request: schemas.StartAuctionRequest, db: Session = Depends(get_db), _ = Depends(verify_key)):
    # First we need to check if the auction ID is valid, make sure the status is not already awarded, and get the item name for the response
    auction_result = db.execute(text("SELECT auctions.name, auction_items.name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.id = :auction_id AND auctions.status != 'awarded'"), {"auction_id": request.auction_id})
    auction_row = auction_result.fetchone()
    print(f"Querying for auction ID: {request.auction_id}. Result: {auction_row}")
    if not auction_row:
        raise HTTPException(status_code=400, detail="Invalid auction ID. Please check the auction ID and try again.")
    auction_name = auction_row[0]
    item_name = auction_row[1]
    print(f"Auction name for auction ID {request.auction_id} is {auction_name} and item name is {item_name}")

    # Then we update the auction to set it as active and set the end time based on the duration in DD/MM/YYYY HH:MM format
    end_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=request.duration_minutes)
    result = db.execute(text("UPDATE auctions SET status = 'active', end_time = :end_time WHERE id = :auction_id returning id"), {"end_time": end_time, "auction_id": request.auction_id})
    updated_auction = result.fetchone()
    if not updated_auction:
        raise HTTPException(status_code=400, detail="Failed to start the auction. Please check the auction ID and try again.")
    
    db.commit()
    return {"status": "started", "auction_id": request.auction_id, "item_name": item_name, "end_time": end_time.isoformat()}

@router.post("/place-bid")
def place_bid(request: schemas.BidRequest, db: Session = Depends(get_db), _ = Depends(verify_key)):
    # First we need to check if the auction ID is valid and get the item name for the response
    auction_result = db.execute(text("SELECT auctions.name, auction_items.name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.id = :auction_id AND auctions.status = 'active'"), {"auction_id": request.auction_id})
    auction_row = auction_result.fetchone()
    print(f"Querying for active auction ID: {request.auction_id}. Result: {auction_row}")
    if not auction_row:
        raise HTTPException(status_code=400, detail="Invalid or inactive auction ID. Please check the auction ID and try again.")
    auction_name = auction_row[0]
    item_name = auction_row[1]
    print(f"Auction name for auction ID {request.auction_id} is {auction_name} and item name is {item_name}")

    # Fetch total balance from lockBox
    query = text('SELECT cruor_amount FROM "lockBox" WHERE member_id = :user_id')
    balance_result = db.execute(query, {"user_id": request.user_id})
    balance_row = balance_result.fetchone()
    balance = balance_row[0] if balance_row else 0

    # Calculate current committed funds (sum of existing bids)
    # This assumes the "bids" table only contains the user's active leading bids.
    query_bids = text('SELECT SUM(amount) FROM bids WHERE user_id = :user_id')
    bids_result = db.execute(query_bids, {"user_id": request.user_id}).fetchone()
    committed_funds = bids_result[0] if bids_result and bids_result[0] else 0

    # Check if current bid + existing bids exceeds balance
    total_commitment = committed_funds + request.amount

    print(f"User {request.user_id}: Balance {balance}, Existing Bids {committed_funds}, New Bid {request.amount}")

    if total_commitment > balance:
        raise HTTPException(
            status_code=400, 
            detail=(
                f"Insufficient balance. Your total committed funds ({total_commitment} Cruor) "
                f"would exceed your balance of {balance} Cruor."
            )
        )    

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

@router.get("/{auction_id}/bids")
def get_bids(auction_id: int, db: Session = Depends(get_db), _ = Depends(verify_key)):
    # First we need to check if the auction ID is valid and get the item name for the response
    auction_result = db.execute(text("SELECT auctions.name, auction_items.name FROM auctions JOIN auction_items ON auctions.item_id = auction_items.id WHERE auctions.id = :auction_id"), {"auction_id": auction_id})
    auction_row = auction_result.fetchone()
    print(f"Querying for auction ID: {auction_id}. Result: {auction_row}")
    if not auction_row:
        raise HTTPException(status_code=400, detail="Invalid auction ID. Please check the auction ID and try again.")
    auction_name = auction_row[0]
    item_name = auction_row[1]
    print(f"Auction name for auction ID {auction_id} is {auction_name} and item name is {item_name}")

    # Then we query the bids for this auction
    bids_result = db.execute(text("SELECT user_id, amount FROM bids WHERE auction_id = :auction_id"), {"auction_id": auction_id})
    bids = [{"user_id": row[0], "amount": row[1]} for row in bids_result.fetchall()]
    return {"auction_id": auction_id, "item_name": item_name, "bids": bids}