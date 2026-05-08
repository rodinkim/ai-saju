from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    category = Column(String, nullable=False)       # wealth / love / couple / …

    # 개인 분석 (항상 채워짐)
    birth_info = Column(String, nullable=False)     # "1992년 8월 26일 17시 30분"
    day_pillar = Column(String, nullable=False)     # "갑신" — 목록 표시용
    four_pillars = Column(JSONB, nullable=False)    # FourPillars.model_dump()

    # 관계 분석 전용 (couple / family / friendship)
    label_a = Column(String, nullable=True)
    label_b = Column(String, nullable=True)
    birth_info_b = Column(String, nullable=True)
    day_pillar_b = Column(String, nullable=True)
    four_pillars_b = Column(JSONB, nullable=True)

    summary = Column(String, nullable=True)         # LLM 생성 요약 (~200자)
    result_text = Column(Text, nullable=True)       # LLM 전문 — 재열람용

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
