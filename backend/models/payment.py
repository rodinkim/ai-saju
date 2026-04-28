from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class Payment(Base):
    __tablename__ = "payments"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id   = Column(String, unique=True, nullable=False)
    payment_key = Column(String, nullable=True)
    amount     = Column(Integer, nullable=False)
    credits    = Column(Integer, nullable=False)
    status     = Column(String, nullable=False, default="done")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
