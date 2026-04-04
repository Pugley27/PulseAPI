import os
from fastapi import FastAPI, HTTPException, Header
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.security.api_key import APIKeyHeader

# Load variables from .env into the system environment
load_dotenv()

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL") # Railway provides this automatically
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


