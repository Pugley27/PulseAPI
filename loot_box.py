from sqlalchemy import create_backend, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base,  IntegrityError, SQLAlchemyError
from pydantic import BaseModel

Base = declarative_base()

# 2. Define your Table (e.g., for Star Citizen materials)
class Material(Base):
  __tablename__ = "materials"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, unique=True)
  quantity = Column(Integer)


# This validates data BEFORE it reaches your DB logic
class MaterialCreate(BaseModel):
  name: str
  quantity: int