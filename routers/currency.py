# This file handles the routing code for tracking member currency.
from sqlalchemy.exc import  IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, verify_key
import schemas
from fastapi import HTTPException, Depends
import datetime

router = APIRouter(
    prefix="/currency",
    tags=["Currency"]
)



@router.post("/add-cruor")
def add_cruor(item: schemas.CruorCreate, db: Session = Depends(get_db), _ = Depends(verify_key)):
    # 1. Try to find the member
    player = db.query(schemas.Cruor).filter(schemas.Cruor.member_id == item.member_id).first()

    if not player:
        # 2. If they don't exist, create them with the starting amount
        new_player = schemas.Cruor(
            member_id=item.member_id,
            cruor_amount=item.cruor_amount,
        )
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        return {"status": "created", "new_balance": new_player.cruor_amount}
    # 3. If they DO exist, just add the amount
    player.cruor_amount += item.cruor_amount
    db.commit()
    db.refresh(player)
    
    return {"status": "updated", "new_balance": player.cruor_amount}
 
