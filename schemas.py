# definitions for tables to hold org currency for members, and the Pydantic models to validate incoming data for those tables.

from sqlalchemy import  Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

# Table holding Cruor amounts for members
class Cruor(Base):
  __tablename__ = "lockBox"
  member_id = Column(Integer, primary_key=True, index=True)
  cruor_amount = Column(Integer)


# This validates data BEFORE it reaches your DB logic
class CruorCreate(BaseModel):
  member_id: int
  cruor_amount: int