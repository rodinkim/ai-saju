from pydantic import BaseModel, Field
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"


class CalendarType(str, Enum):
    solar = "solar"    # 양력
    lunar = "lunar"    # 음력


class SajuRequest(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="출생 연도")
    month: int = Field(..., ge=1, le=12, description="출생 월")
    day: int = Field(..., ge=1, le=31, description="출생 일")
    hour: int = Field(..., ge=0, le=23, description="출생 시각 (24시간)")
    minute: int = Field(0, ge=0, le=59, description="출생 분")
    gender: Gender = Field(..., description="성별")
    calendar_type: CalendarType = Field(CalendarType.solar, description="양력/음력")
    is_leap_month: bool = Field(False, description="음력 윤달 여부 (calendar_type=lunar 일 때만 적용)")
    category: str = Field("free", description="분석 카테고리 (free / wealth / love)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "year": 1992,
                "month": 8,
                "day": 26,
                "hour": 17,
                "minute": 30,
                "gender": "male",
                "calendar_type": "solar",
            }
        }
    }


class Pillar(BaseModel):
    """사주 하나의 기둥 (천간 + 지지)"""
    heavenly_stem: str = Field(..., description="천간 (甲乙丙丁戊己庚辛壬癸)")
    earthly_branch: str = Field(..., description="지지 (子丑寅卯辰巳午未申酉戌亥)")
    korean: str = Field(..., description="한글 표기 (예: 갑자)")


class SinsalItem(BaseModel):
    """신살 항목 (이름 + 발동 주)"""
    name: str = Field(..., description="신살 이름 (예: 역마살)")
    pillar: str = Field(..., description="발동 주 (년/월/일/시)")
    basis: str = Field(..., description="산출 기준 (예: 년지기준/일지기준/일주기준/일간기준)")

class GwiinItem(BaseModel):
    """귀인 항목 상세"""
    name: str = Field(..., description="귀인 이름 (예: 천을귀인)")
    basis: str = Field(..., description="산출 기준 (예: 일간기준/월지기준/천간조합기준)")
    matched: list[str] = Field(default_factory=list, description="매칭된 요소 목록 (예: 년지:丑, 월간:甲)")
    weakened: bool = Field(False, description="충/공망 등으로 약화 여부")
    weaken_reason: str = Field("", description="약화 사유 (충/공망)")


class FourPillars(BaseModel):
    """사주팔자 (년주·월주·일주·시주)"""
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar
    gwiin: list[str] = Field(default_factory=list, description="귀인 목록")
    gwiin_details: list[GwiinItem] = Field(default_factory=list, description="귀인 상세 목록")
    sinsal: list[SinsalItem] = Field(default_factory=list, description="신살 목록")


class SajuResponse(BaseModel):
    four_pillars: FourPillars = Field(..., description="사주팔자")
    analysis: str = Field(..., description="사주 풀이 텍스트")
    summary: str = Field(..., description="한 줄 요약")
