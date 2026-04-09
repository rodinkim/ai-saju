import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from korean_lunar_calendar import KoreanLunarCalendar
from schemas.saju import SajuRequest, SajuResponse, CalendarType, FourPillars, Pillar, SinsalItem, GwiinItem
from services.llm import analyze_with_llm, stream_with_llm, _parse_analysis
from services.rag import search_relevant_theory
from services.sinsal import calculate_gwiin_sinsal

router = APIRouter(prefix="/api/saju", tags=["사주 분석"])

# 천간 (10개)
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
HEAVENLY_STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

# 지지 (12개)
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
EARTHLY_BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]


def get_year_pillar(year: int) -> Pillar:
    """
    년주 계산.
    기준: 1984년 = 甲子(갑자)
    천간 주기 10, 지지 주기 12 → 60갑자 반복
    """
    base_year = 1984  # 甲子년
    offset = (year - base_year) % 60
    stem_idx = offset % 10
    branch_idx = offset % 12
    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


# 절기(節氣) 기준일 (월, 일) — 평균 근사값 ±1~2일
# 각 절기가 해당 사주 월의 시작점
JEOLGI_DATES = [(1,6),(2,4),(3,6),(4,5),(5,6),(6,6),(7,7),(8,7),(9,8),(10,8),(11,7),(12,7)]
# 절기 순서에 대응하는 지지 인덱스: 소한=丑(1), 입춘=寅(2), ..., 대설=子(0)
JEOLGI_BRANCH = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]

def _get_saju_month(month: int, day: int) -> tuple[int, int]:
    """절기 기준 (지지 인덱스, 사주 월 번호 1=寅~12=丑) 반환"""
    jeolgi_day = JEOLGI_DATES[month - 1][1]
    if day >= jeolgi_day:
        branch_idx = JEOLGI_BRANCH[month - 1]
    else:
        prev = month - 2 if month > 1 else 11   # JEOLGI_BRANCH 인덱스 (0-based)
        branch_idx = JEOLGI_BRANCH[prev]
    saju_month_num = (branch_idx - 2 + 12) % 12 + 1  # 寅=1 ... 丑=12
    return branch_idx, saju_month_num


def get_month_pillar(year: int, month: int, day: int) -> Pillar:
    """
    월주 계산.
    절기(節氣) 기준으로 사주 월을 결정한 뒤 오호둔월법(五虎遁月法)으로 천간 산출.
    """
    base_year = 1984
    year_stem_idx = (year - base_year) % 10

    branch_idx, saju_month_num = _get_saju_month(month, day)

    # 오호둔월법: 년 천간을 % 5로 그룹핑 (甲己/乙庚/丙辛/丁壬/戊癸)
    month_stem_base = [2, 4, 6, 8, 0]  # 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
    stem_start = month_stem_base[year_stem_idx % 5]
    stem_idx = (stem_start + saju_month_num - 1) % 10

    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def get_day_pillar(year: int, month: int, day: int) -> Pillar:
    """
    일주 계산.
    율리우스 적일(Julian Day Number)을 이용해 60갑자 순환.
    기준: 1900-01-01 = 甲戌(갑술) → JDN 2415021, offset 10(甲) + 11(戌)
    """
    # Zeller's 공식으로 JDN 계산
    if month < 3:
        month += 12
        year -= 1
    a = year // 100
    b = 2 - a + a // 4
    jdn = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524

    base_jdn = 2415021  # 1900-01-01
    base_stem = 10      # (10 % 10 = 0) → 甲
    base_branch = 10    # 戌 index (index 10)

    offset = jdn - base_jdn
    stem_idx = (base_stem + offset) % 10
    branch_idx = (base_branch + offset) % 12

    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def get_hour_pillar(day_stem_idx: int, hour: int, minute: int = 0) -> Pillar:
    """
    시주 계산.
    시지: 23~00시=子(자), 01~02시=丑(축), ... 2시간 단위
    경계(정각 기준 30분)는 다음 시로 넘어감 — 예: 00:30 → 丑시
    시간은 오자둔시법 적용
    """
    # 전통 시 경계: 子時 23:30~01:29, 申時 15:30~17:29 ...
    # 30분을 빼서 정시 기준으로 환산 후 2시간 단위로 나눔
    total_min = hour * 60 + minute
    adjusted_hour = ((total_min - 30) % 1440) // 60

    branch_idx = ((adjusted_hour + 1) // 2) % 12

    # 오자둔시법: 일 천간 그룹에 따라 자시(子時) 천간 결정
    hour_stem_base = [0, 2, 4, 6, 8]  # 甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子
    stem_start = hour_stem_base[day_stem_idx % 5]
    stem_idx = (stem_start + branch_idx) % 10

    return Pillar(
        heavenly_stem=HEAVENLY_STEMS[stem_idx],
        earthly_branch=EARTHLY_BRANCHES[branch_idx],
        korean=HEAVENLY_STEMS_KR[stem_idx] + EARTHLY_BRANCHES_KR[branch_idx],
    )


def calculate_four_pillars(req: SajuRequest) -> FourPillars:
    year_pillar  = get_year_pillar(req.year)
    month_pillar = get_month_pillar(req.year, req.month, req.day)
    day_pillar   = get_day_pillar(req.year, req.month, req.day)

    day_stem_idx = HEAVENLY_STEMS.index(day_pillar.heavenly_stem)
    hour_pillar  = get_hour_pillar(day_stem_idx, req.hour, req.minute)

    fp_base = FourPillars(
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
    )
    gwiin, gwiin_details_raw, sinsal_raw = calculate_gwiin_sinsal(fp_base)

    return FourPillars(
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
        gwiin=gwiin,
        gwiin_details=[
            GwiinItem(
                name=g["name"],
                basis=g["basis"],
                matched=g.get("matched", []),
                weakened=g.get("weakened", False),
                weaken_reason=g.get("weaken_reason", ""),
            ) for g in gwiin_details_raw
        ],
        sinsal=[SinsalItem(name=s["name"], pillar=s["pillar"], basis=s["basis"]) for s in sinsal_raw],
    )


def _lunar_to_solar(year: int, month: int, day: int, is_leap: bool) -> tuple[int, int, int]:
    """음력 날짜를 양력으로 변환. 변환 실패 시 HTTPException 발생."""
    cal = KoreanLunarCalendar()
    ok = cal.setLunarDate(year, month, day, is_leap)
    if not ok:
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 음력 날짜입니다: {year}년 {month}월 {day}일{'(윤달)' if is_leap else ''}",
        )
    return cal.solarYear, cal.solarMonth, cal.solarDay


@router.post("/analyze", response_model=SajuResponse)
async def analyze_saju(req: SajuRequest):
    """
    사주팔자 분석.
    0단계: 음력이면 양력으로 변환
    1단계: 만세력 계산 (사주팔자 산출)
    2단계: Claude API 기반 해석
    """
    solar_year, solar_month, solar_day = req.year, req.month, req.day
    lunar_info = ""

    if req.calendar_type == CalendarType.lunar:
        solar_year, solar_month, solar_day = _lunar_to_solar(
            req.year, req.month, req.day, req.is_leap_month
        )
        leap_str = "(윤달)" if req.is_leap_month else ""
        lunar_info = f" [음력 {req.year}년 {req.month}월 {req.day}일{leap_str} → 양력 {solar_year}년 {solar_month}월 {solar_day}일]"

        # 양력으로 변환된 값으로 req를 재구성 (immutable 우회)
        req = req.model_copy(update={"year": solar_year, "month": solar_month, "day": solar_day})

    four_pillars = calculate_four_pillars(req)

    birth_info = f"{solar_year}년 {solar_month}월 {solar_day}일 {req.hour}시 {req.minute}분{lunar_info}"
    rag_context = search_relevant_theory(four_pillars)
    try:
        analysis, summary = await analyze_with_llm(four_pillars, req.gender, birth_info, rag_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 분석 실패: {str(e)}")

    return SajuResponse(
        four_pillars=four_pillars,
        analysis=analysis,
        summary=summary,
    )


@router.post("/analyze/stream")
async def analyze_saju_stream(req: SajuRequest):
    """
    사주팔자 스트리밍 분석 (SSE).
    이벤트 타입:
      pillars — 사주팔자 원국 JSON (즉시 전송)
      delta   — LLM 텍스트 청크
      done    — 완료 신호 + summary
      error   — 오류 메시지
    """
    print(f"[STREAM] 함수 진입 year={req.year} category={req.category}", flush=True)
    solar_year, solar_month, solar_day = req.year, req.month, req.day
    lunar_info = ""

    if req.calendar_type == CalendarType.lunar:
        solar_year, solar_month, solar_day = _lunar_to_solar(
            req.year, req.month, req.day, req.is_leap_month
        )
        leap_str = "(윤달)" if req.is_leap_month else ""
        lunar_info = f" [음력 {req.year}년 {req.month}월 {req.day}일{leap_str} → 양력 {solar_year}년 {solar_month}월 {solar_day}일]"
        req = req.model_copy(update={"year": solar_year, "month": solar_month, "day": solar_day})

    four_pillars = calculate_four_pillars(req)
    birth_info = f"{solar_year}년 {solar_month}월 {solar_day}일 {req.hour}시 {req.minute}분{lunar_info}"
    rag_context = search_relevant_theory(four_pillars)

    def sse(event: str, data) -> str:
        # JSON 인코딩: delta에 \n\n 포함 시 SSE 파서 오작동 방지
        payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"

    is_free = req.category == "free"
    print(f"[REQ] category={req.category} model={'haiku' if is_free else 'sonnet'} birth={birth_info}", flush=True)

    async def event_stream():
        # 1) 원국 즉시 전송
        yield sse("pillars", four_pillars.model_dump())

        # 2) LLM 스트리밍
        full_text = ""
        try:
            async for chunk in stream_with_llm(four_pillars, req.gender, birth_info, rag_context, free=is_free):
                full_text += chunk
                yield sse("delta", chunk)
        except Exception as e:
            print(f"[ERR] LLM 스트리밍 실패: {e}")
            yield sse("error", str(e))
            return

        print(f"[RES] 생성 완료 | 텍스트 길이={len(full_text)}자")

        # 3) 완료: summary 파싱 후 전송
        analysis, summary = _parse_analysis(full_text)
        yield sse("done", {"summary": summary})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
