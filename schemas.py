# definitions for tables to hold org currency for members, and the Pydantic models to validate incoming data for those tables.


from sqlalchemy import  BigInteger, Column, TIMESTAMP, DateTime, Integer, BigInteger, String, Boolean
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
  __tablename__ = "auction_items"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  description = Column(String)
  status = Column(String)
  auction_id = Column(Integer)
  member_id = Column(BigInteger)
  holder_id = Column(BigInteger)

class Auctions(Base):
  __tablename__ = "auctions"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  description = Column(String)  
  item_id = Column(Integer)
  start_time = Column(DateTime(timezone=True))
  end_time = Column(DateTime(timezone=True))
  status = Column(String)
  winner_id = Column(BigInteger)
  holder_id = Column(BigInteger)

class Bids(Base):
  __tablename__ = "bids"
  auction_id = Column(Integer, primary_key=True, index=True)
  user_id = Column(BigInteger, primary_key=True, index=True)
  amount = Column(Integer)
  
class BidRequest(BaseModel):
  user_id: int
  auction_id: int
  amount: int

class AuctionBids(BaseModel):
  user_id: int
  
class ItemCreate(BaseModel):
  name : str
  description: str
  holder_id: int

class AuctionCreate(BaseModel):
  name: str
  description: str
  item_id: int

class StartAuctionRequest(BaseModel):
  auction_id: int
  duration_minutes: int

#class that will create all the tables in the database if they don't already exist. This is called in main.py when the bot starts up to make sure the tables are ready to go before any commands are used.
def create_tables(engine):
    Base.metadata.create_all(bind=engine) 