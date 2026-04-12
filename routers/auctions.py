from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db

router = APIRouter(
    prefix="/auctions",
    tags=["auctions"]
)

class BidRequest(BaseModel):
    user_id: int
    amount: int
    item_name: str

@router.post("/bid")
async def place_bid(bid: BidRequest):
    conn = get_db()
    cur = conn.cursor()
    
    # Check balance from the players table
    cur.execute("SELECT balance FROM players WHERE user_id = %s", (bid.user_id,))
    res = cur.fetchone()
    balance = res[0] if res else 0
    
    if bid.amount > balance:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient Cruor")

    # Record the bid
    cur.execute('''
        INSERT INTO bids (user_id, item_name, amount) VALUES (%s, %s, %s)
        ON CONFLICT (user_id, item_name) DO UPDATE SET amount = EXCLUDED.amount
    ''', (bid.user_id, bid.item_name, bid.amount))
    
    conn.commit()
    conn.close()
    return {"status": "bid_accepted"}
4. main.py (The Glue)
Now, your main file becomes incredibly clean. It just imports the routers and tells FastAPI to use them.

Python
from fastapi import FastAPI
from routers import bank, auctions # Import your sub-files

app = FastAPI(title="Cruor Loot API")

# Include the routers
app.include_router(bank.router)
app.include_router(auctions.router)

@app.get("/")
async def root():
    return {"message": "Cruor API is online and healthy."}