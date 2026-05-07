from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)        # kakao / naver / google
    provider_id = Column(String, nullable=False)     # 각 플랫폼의 고유 user id
    email = Column(String, nullable=True, unique=True)
    name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    credits = Column(Integer, nullable=False, default=30, server_default="30")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("provider", "provider_id"),
    )
