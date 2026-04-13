# definitions for tables to hold org currency for members, and the Pydantic models to validate incoming data for those tables.

from sqlalchemy import  BigInteger, Column, Integer, BigInteger, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

# Table holding Cruor amounts for members
class Cruor(Base):
  __tablename__ = "lockBox"
  member_id = Column(BigInteger, primary_key=True, index=True)
  display_name = Column(String)
  cruor_amount = Column(Integer)


# This validates data BEFORE it reaches your DB logic
class CruorCreate(BaseModel):
  member_id: int
  display_name: str
  cruor_amount: int

class CheckBalance(BaseModel):
  member_id: int


#Table holding items for auction
class AuctionItems(Base):
  __tablename__ = "auctionItems"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  description = Column(String)

class Auctions(Base):
  __tablename__ = "auctions"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  description = Column(String)  
  item_id = Column(Integer)
  start_time = Column(BigInteger)
  end_time = Column(BigInteger)
  active = Column(Boolean)
  
class BidRequest(BaseModel):
  user_id: int
  amount: int
  item_name: str

class ItemCreate(BaseModel):
  name : str
  description: str

class AuctionCreate(BaseModel):
  name: str
  description: str
  item_id: int
