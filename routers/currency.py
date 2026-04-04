# This file handles the routing code for tracking member currency.
from sqlalchemy.exc import  IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, verify_key
import schemas
from fastapi import HTTPException, Depends

router = APIRouter(
    prefix="/currency",
    tags=["Currency"]
)

@router.post("/add-cruor")
def add_cruor(item: schemas.CruorCreate, db: Session = Depends(get_db), _ = Depends(verify_key)):
    new_item = schemas.Cruor(member_id=item.member_id, cruor_amount=item.cruor_amount)
    try:
        db.add(new_item)
        db.commit()  # The database validates constraints here
        db.refresh(new_item)
        return new_item
    except IntegrityError as e:
        db.rollback()  # Crucial: Unlocks the session
        # Handle specific DB errors like "Already Exists"
    raise HTTPException(
        status_code=400, 
        detail="Item already exists or violates database constraints.")
    return {"status": "success"}

 
