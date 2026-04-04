import os
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy import create_backend, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base,  IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import loot_box 

# 1. Database Setup
DATABASE_URL = os.getenv("DATABASE_URL") # Railway provides this automatically
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


app = FastAPI()
# Dependency to get DB session
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

API_KEY = os.getenv("SECRET_API_KEY") # Set this in Railway Variables
def verify_key(x_api_key: str = Header(...)):
  if x_api_key != API_KEY:
    raise HTTPException(status_code=403, detail="Invalid API Key")
                    
@app.post("/add-material/")
def add_material(item: loot_box.MaterialCreate, db: Session = Depends(get_db), _ = Depends(verify_key)):
  new_item = loot_box.Material(name=item.name, quantity=item.qty)
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
