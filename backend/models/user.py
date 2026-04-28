from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)        # kakao / naver / google
    provider_id = Column(String, nullable=False)     # 각 플랫폼의 고유 user id
    email = Column(String, nullable=True)
    name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    credits = Column(Integer, nullable=False, default=100, server_default="100")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        # (provider, provider_id) 조합은 유일
        __import__("sqlalchemy").UniqueConstraint("provider", "provider_id"),
    )
