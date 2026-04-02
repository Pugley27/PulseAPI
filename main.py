import os
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy import create_backend, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 1. Database Setup
DATABASE_URL = os.getenv("DATABASE_URL") # Railway provides this automatically
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Define your Table (e.g., for Star Citizen materials)
class Material(Base):
  __tablename__ = "materials"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, unique=True)
  quantity = Column(Integer)

Base.metadata.create_all(bind=engine)
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
def add_material(name: str, qty: int, db: Session = Depends(get_db), _ = Depends(verify_key)):
  new_item = Material(name=name, quantity=qty)
  db.add(new_item)
  db.commit()
  db.refresh(new_item)
  return {"status": "success", "data": new_item
