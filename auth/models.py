from sqlalchemy import Column , Integer , String , Boolean , ForeignKey , DateTime
from sqlalchemy.orm import relationship
from database.database import Base
from typing import Dict , Any 

class User(Base):
    __tablename__="user"
    id=Column(Integer , primary_key=True, index=True)
    email=Column(String, unique=True, index=True)
    otp=Column(String, nullable=True)
    otp_created_at = Column(DateTime , nullable=True)
    is_verified=Column(Boolean , default=False)

    # subscription 
    blog = relationship("BlogContent", back_populates="user" ,uselist=False)


    def __str__(self)->str:
        return f"User(id={self.id} , email={self.email} "
    
    @property
    def safe_data(self)-> Dict[str, Any]:
        return {
            "id":self.id ,
            "email":self.email,
            "username":self.username,
            "is_verified":self.is_verified
        }