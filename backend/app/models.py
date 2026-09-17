from sqlalchemy import Column, Integer, String
from app.database import Base

class Quest(Base):
    __tablename__ = "quests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    domain_id = Column(Integer, nullable=False)
    difficulty = Column(String)
    xp_reward = Column(Integer, nullable=False)