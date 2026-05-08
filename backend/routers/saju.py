import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from korean_lunar_calendar import KoreanLunarCalendar
from sqlalchemy.orm import Session
from schemas.saju import (
    SajuRequest, CalendarType, FourPillars, PersonInfo, RelationRequest,
    AnalysisItem, AnalysisDetail,
)
from services.llm import stream_with_llm, stream_relation_with_llm, _parse_analysis
from services.pillars import calculate_four_pillars
from services.rag import search_relevant_theory
from database import get_db
from models.user import User
from models.analysis import Analysis
from routers.auth import require_current_user

router = APIRouter(prefix="/api/saju", tags=["사주 분석"])


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


@router.post("/analyze/stream")
async def analyze_saju_stream(
    req: SajuRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """
    사주팔자 스트리밍 분석 (SSE).
    이벤트 타입:
      pillars — 사주팔자 원국 JSON (즉시 전송)
      delta   — LLM 텍스트 청크
      done    — 완료 신호 + summary
      error   — 오류 메시지
    """
    if current_user.credits < 10:
        raise HTTPException(status_code=402, detail="크레딧이 부족합니다. 충전 후 이용해주세요.")

    # 사주 계산 / RAG 검색을 크레딧 차감 전에 수행
    # → 이 단계에서 실패하면 크레딧 소모 없음
    solar_year, solar_month, solar_day = req.year, req.month, req.day
    lunar_info = ""

    if req.calendar_type == CalendarType.lunar:
        solar_year, solar_month, solar_day = _lunar_to_solar(
            req.year, req.month, req.day, req.is_leap_month
        )
        leap_str = "(윤달)" if req.is_leap_month else ""
        lunar_info = f" [음력 {req.year}년 {req.month}월 {req.day}일{leap_str} → 양력 {solar_year}년 {solar_month}월 {solar_day}일]"
        req = req.model_copy(update={"year": solar_year, "month": solar_month, "day": solar_day})

    four_pillars = calculate_four_pillars(solar_year, solar_month, solar_day, req.hour, req.minute)
    birth_info = f"{solar_year}년 {solar_month}월 {solar_day}일 {req.hour}시 {req.minute}분{lunar_info}"
    rag_context = search_relevant_theory(four_pillars, category=req.category)

    # 모든 사전 작업 성공 후 크레딧 차감
    current_user.credits -= 10
    db.commit()

    print(f"[STREAM] year={req.year} category={req.category} user={current_user.id} credits_left={current_user.credits}", flush=True)
    print(f"[REQ] category={req.category} birth={birth_info}", flush=True)

    def sse(event: str, data) -> str:
        payload = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {payload}\n\n"

    async def event_stream():
        # 1) 원국 즉시 전송
        yield sse("pillars", four_pillars.model_dump())

        # 2) LLM 스트리밍 — 실패 시 크레딧 환불
        full_text = ""
        try:
            async for chunk in stream_with_llm(
                four_pillars,
                req.gender,
                solar_year,
                solar_month,
                solar_day,
                birth_info,
                rag_context,
                category=req.category,
            ):
                full_text += chunk
                yield sse("delta", chunk)
        except Exception as e:
            print(f"[ERR] LLM 스트리밍 실패: {e}")
            current_user.credits += 10
            db.commit()
            yield sse("error", str(e))
            return

        print(f"[RES] 생성 완료 | 텍스트 길이={len(full_text)}자")

        # 3) 완료: summary 파싱 후 전송
        _, summary = _parse_analysis(full_text)
        yield sse("done", {"summary": summary})

        # 4) 분석 이력 저장 (실패해도 응답에 영향 없음)
        try:
            db.add(Analysis(
                user_id=current_user.id,
                category=req.category,
                birth_info=birth_info,
                day_pillar=four_pillars.day_pillar.korean,
                four_pillars=four_pillars.model_dump(),
                summary=summary,
                result_text=full_text,
            ))
            db.commit()
        except Exception as e:
            print(f"[WARN] 분석 이력 저장 실패: {e}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _resolve_person(p: PersonInfo) -> tuple[FourPillars, int, int, int, str]:
    """PersonInfo → (FourPillars, solar_year, solar_month, solar_day, birth_info)"""
    solar_year, solar_month, solar_day = p.year, p.month, p.day
    lunar_info = ""

    if p.calendar_type == CalendarType.lunar:
        solar_year, solar_month, solar_day = _lunar_to_solar(p.year, p.month, p.day, p.is_leap_month)
        leap_str = "(윤달)" if p.is_leap_month else ""
        lunar_info = f" [음력 {p.year}년 {p.month}월 {p.day}일{leap_str} → 양력 {solar_year}년 {solar_month}월 {solar_day}일]"

    four_pillars = calculate_four_pillars(solar_year, solar_month, solar_day, p.hour, p.minute)
    birth_info = f"{solar_year}년 {solar_month}월 {solar_day}일 {p.hour}시 {p.minute}분{lunar_info}"
    return four_pillars, solar_year, solar_month, solar_day, birth_info


VALID_RELATION_CATEGORIES = {"couple", "family", "friendship"}


@router.post("/relation/stream")
async def relation_stream(
    req: RelationRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """
    두 사람 관계 사주 스트리밍 분석 (SSE).
    category: couple(궁합) / family(가족) / friendship(우정)
    이벤트: pillars_a, pillars_b, delta, done, error
    """
    if req.category not in VALID_RELATION_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"category는 {VALID_RELATION_CATEGORIES} 중 하나여야 합니다.")

    if current_user.credits < 10:
        raise HTTPException(status_code=402, detail="크레딧이 부족합니다. 충전 후 이용해주세요.")

    # 사주 계산 / RAG 검색을 크레딧 차감 전에 수행
    fp_a, sy_a, sm_a, sd_a, bi_a = _resolve_person(req.person_a)
    fp_b, sy_b, sm_b, sd_b, bi_b = _resolve_person(req.person_b)

    rag_a = search_relevant_theory(fp_a, category=req.category)
    rag_b = search_relevant_theory(fp_b, category=req.category)
    rag_context = "\n".join(filter(None, [rag_a, rag_b]))

    # 모든 사전 작업 성공 후 크레딧 차감
    current_user.credits -= 10
    db.commit()

    def sse(event: str, data) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_stream():
        yield sse("pillars_a", fp_a.model_dump())
        yield sse("pillars_b", fp_b.model_dump())

        full_text = ""
        try:
            async for chunk in stream_relation_with_llm(
                fp_a, fp_b,
                req.person_a.label, req.person_b.label,
                req.person_a.gender, req.person_b.gender,
                bi_a, bi_b,
                sy_a, sm_a, sd_a,
                sy_b, sm_b, sd_b,
                rag_context,
                category=req.category,
            ):
                full_text += chunk
                yield sse("delta", chunk)
        except Exception as e:
            print(f"[ERR] 관계 LLM 스트리밍 실패: {e}")
            current_user.credits += 10
            db.commit()
            yield sse("error", str(e))
            return

        _, summary = _parse_analysis(full_text)
        yield sse("done", {"summary": summary})

        # 분석 이력 저장 (실패해도 응답에 영향 없음)
        try:
            db.add(Analysis(
                user_id=current_user.id,
                category=req.category,
                birth_info=bi_a,
                day_pillar=fp_a.day_pillar.korean,
                four_pillars=fp_a.model_dump(),
                label_a=req.person_a.label or None,
                label_b=req.person_b.label or None,
                birth_info_b=bi_b,
                day_pillar_b=fp_b.day_pillar.korean,
                four_pillars_b=fp_b.model_dump(),
                summary=summary,
                result_text=full_text,
            ))
            db.commit()
        except Exception as e:
            print(f"[WARN] 관계 분석 이력 저장 실패: {e}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=list[AnalysisItem])
async def get_history(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """분석 이력 목록 조회 (최신순, 기본 20개)."""
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        AnalysisItem(
            id=r.id,
            category=r.category,
            birth_info=r.birth_info,
            day_pillar=r.day_pillar,
            label_a=r.label_a,
            label_b=r.label_b,
            birth_info_b=r.birth_info_b,
            day_pillar_b=r.day_pillar_b,
            summary=r.summary,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/history/{analysis_id}", response_model=AnalysisDetail)
async def get_history_detail(
    analysis_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """분석 이력 상세 조회 (전문 포함)."""
    row = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="분석 이력을 찾을 수 없습니다.")
    return AnalysisDetail(
        id=row.id,
        category=row.category,
        birth_info=row.birth_info,
        day_pillar=row.day_pillar,
        label_a=row.label_a,
        label_b=row.label_b,
        birth_info_b=row.birth_info_b,
        day_pillar_b=row.day_pillar_b,
        summary=row.summary,
        created_at=row.created_at.isoformat(),
        four_pillars=row.four_pillars,
        four_pillars_b=row.four_pillars_b,
        result_text=row.result_text,
    )
