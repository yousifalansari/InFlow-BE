from sqlalchemy import Column, Integer, String, Enum
from .base import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import jwt
from config.environment import secret
# Associations
from sqlalchemy.orm import relationship


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserModel(BaseModel):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=True)
    # role = Column(Enum(Role), default=Role.OWNER)
    role = Column(String, default="owner", nullable=False)

    # hoots = relationship('HootModel', back_populates='user', cascade='all, delete-orphan')
    # comments = relationship('CommentModel', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    def generate_token(self):
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "iat": datetime.now(timezone.utc),
            "sub": str(self.id),
        }

        token = jwt.encode(payload, secret, algorithm="HS256")

        return token
