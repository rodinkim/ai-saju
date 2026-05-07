import re
import time
from datetime import date
from pathlib import Path
from typing import AsyncIterator
from anthropic import AsyncAnthropic

import settings
from schemas.saju import FourPillars, Gender
from services.ganji import year_ganji as _year_ganji  # noqa: F401 — used via _year_ganji alias

client = AsyncAnthropic(api_key=settings.get_anthropic_api_key())

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

MODEL = settings.get_llm_model()
MAX_TOKENS = 6000

_prompt_cache: dict[str, str] = {}

def _load(filename: str) -> str:
    if filename not in _prompt_cache:
        _prompt_cache[filename] = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return _prompt_cache[filename]


def _cached_system(text: str) -> list[dict]:
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


_KNOWN_CATEGORIES = {"love", "wealth", "fortune", "pastlife", "vocation", "daewoon"}

def _category_prompt_files(category: str) -> tuple[str, str, str | None]:
    if category in _KNOWN_CATEGORIES:
        return f"{category}_analyze_user.txt", f"{category}_system.txt", None
    return "wealth_analyze_user.txt", "wealth_system.txt", None


def _relation_prompt_files(category: str) -> tuple[str, str]:
    return f"{category}_analyze_user.txt", f"{category}_system.txt"


def _international_age(birth_year: int, birth_month: int, birth_day: int, ref: date) -> int:
    """만 나이 (양력 생일 기준, ref 날짜 시점)."""
    age = ref.year - birth_year
    if (ref.month, ref.day) < (birth_month, birth_day):
        age -= 1
    return max(0, age)


def _year_counting_age(birth_year: int, ref: date) -> int:
    """세는 나이(연 나이, 양력 연도 기준: ref.year - birth_year + 1)."""
    return ref.year - birth_year + 1


def _build_user_message(
    template: str,
    fp: FourPillars,
    gender: Gender,
    birth_info: str,
    rag_context: str,
    birth_year: int,
    birth_month: int,
    birth_day: int,
) -> str:
    ref = date.today()
    return template.format(
        birth_info=birth_info,
        gender="남성" if gender == Gender.male else "여성",
        current_year=ref.year,
        current_year_korean=_year_ganji(ref.year),
        reference_date_iso=ref.isoformat(),
        age_international=_international_age(birth_year, birth_month, birth_day, ref),
        age_korean=_year_counting_age(birth_year, ref),
        year_korean=fp.year_pillar.korean,   year_stem=fp.year_pillar.heavenly_stem,   year_branch=fp.year_pillar.earthly_branch,
        month_korean=fp.month_pillar.korean, month_stem=fp.month_pillar.heavenly_stem, month_branch=fp.month_pillar.earthly_branch,
        day_korean=fp.day_pillar.korean,     day_stem=fp.day_pillar.heavenly_stem,     day_branch=fp.day_pillar.earthly_branch,
        hour_korean=fp.hour_pillar.korean,   hour_stem=fp.hour_pillar.heavenly_stem,   hour_branch=fp.hour_pillar.earthly_branch,
        rag_context=rag_context,
    )


def _build_relation_user_message(
    template: str,
    fp_a: "FourPillars",
    fp_b: "FourPillars",
    label_a: str,
    label_b: str,
    gender_a: "Gender",
    gender_b: "Gender",
    birth_info_a: str,
    birth_info_b: str,
    birth_year_a: int, birth_month_a: int, birth_day_a: int,
    birth_year_b: int, birth_month_b: int, birth_day_b: int,
    rag_context: str,
) -> str:
    ref = date.today()
    return template.format(
        label_a=label_a or "A",
        label_b=label_b or "B",
        birth_info_a=birth_info_a,
        birth_info_b=birth_info_b,
        gender_a="남성" if gender_a == Gender.male else "여성",
        gender_b="남성" if gender_b == Gender.male else "여성",
        current_year=ref.year,
        current_year_korean=_year_ganji(ref.year),
        age_a=_international_age(birth_year_a, birth_month_a, birth_day_a, ref),
        age_b=_international_age(birth_year_b, birth_month_b, birth_day_b, ref),
        year_korean_a=fp_a.year_pillar.korean,   year_stem_a=fp_a.year_pillar.heavenly_stem,   year_branch_a=fp_a.year_pillar.earthly_branch,
        month_korean_a=fp_a.month_pillar.korean, month_stem_a=fp_a.month_pillar.heavenly_stem, month_branch_a=fp_a.month_pillar.earthly_branch,
        day_korean_a=fp_a.day_pillar.korean,     day_stem_a=fp_a.day_pillar.heavenly_stem,     day_branch_a=fp_a.day_pillar.earthly_branch,
        hour_korean_a=fp_a.hour_pillar.korean,   hour_stem_a=fp_a.hour_pillar.heavenly_stem,   hour_branch_a=fp_a.hour_pillar.earthly_branch,
        year_korean_b=fp_b.year_pillar.korean,   year_stem_b=fp_b.year_pillar.heavenly_stem,   year_branch_b=fp_b.year_pillar.earthly_branch,
        month_korean_b=fp_b.month_pillar.korean, month_stem_b=fp_b.month_pillar.heavenly_stem, month_branch_b=fp_b.month_pillar.earthly_branch,
        day_korean_b=fp_b.day_pillar.korean,     day_stem_b=fp_b.day_pillar.heavenly_stem,     day_branch_b=fp_b.day_pillar.earthly_branch,
        hour_korean_b=fp_b.hour_pillar.korean,   hour_stem_b=fp_b.hour_pillar.heavenly_stem,   hour_branch_b=fp_b.hour_pillar.earthly_branch,
        rag_context=rag_context,
    )


async def stream_relation_with_llm(
    fp_a: "FourPillars",
    fp_b: "FourPillars",
    label_a: str,
    label_b: str,
    gender_a: "Gender",
    gender_b: "Gender",
    birth_info_a: str,
    birth_info_b: str,
    birth_year_a: int, birth_month_a: int, birth_day_a: int,
    birth_year_b: int, birth_month_b: int, birth_day_b: int,
    rag_context: str = "",
    category: str = "couple",
) -> AsyncIterator[str]:
    user_file, system_file = _relation_prompt_files(category)
    user_template = _load(user_file)
    system = _load(system_file)

    user_message = _build_relation_user_message(
        user_template,
        fp_a, fp_b,
        label_a, label_b,
        gender_a, gender_b,
        birth_info_a, birth_info_b,
        birth_year_a, birth_month_a, birth_day_a,
        birth_year_b, birth_month_b, birth_day_b,
        rag_context,
    )
    messages = [{"role": "user", "content": user_message}]

    print(f"[LLM] 관계 스트림 | category={category} | prompt={len(user_message)}자", flush=True)

    t0 = time.perf_counter()
    ttft: float | None = None

    async with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=_cached_system(system),
        messages=messages,
    ) as stream:
        async for delta in stream.text_stream:
            if ttft is None:
                ttft = time.perf_counter() - t0
            yield delta
        try:
            final = await stream.get_final_message()
            total = time.perf_counter() - t0
            u = final.usage
            cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
            cache_write = getattr(u, "cache_creation_input_tokens", 0) or 0
            print(
                f"[LLM] 관계 스트림 완료 | {total:.2f}s (TTFT {ttft:.2f}s)"
                f" | in={u.input_tokens} out={u.output_tokens}"
                f" | cache_read={cache_read} cache_write={cache_write}",
                flush=True,
            )
        except Exception as e:
            print(f"[LLM] get_final_message 실패: {e}")


def _parse_analysis(full_text: str) -> tuple[str, str]:
    """LLM 응답에서 H1 제목·원국 섹션을 제거하고 (analysis, summary)로 분리."""
    if re.match(r'^#\s', full_text):
        sections = re.split(r'(?m)(?=^##\s)', full_text, flags=re.MULTILINE)
        filtered = [
            s for s in sections
            if not re.match(r'^#\s', s)
            and not re.search(r'구성|원국|기본\s*정보|생년월일', s[:80])
        ]
        if filtered:
            full_text = ''.join(filtered).strip()

    if "[요약]" in full_text:
        parts = full_text.split("[요약]", 1)
        return parts[0].strip(), parts[1].strip()

    return full_text, full_text[:80] + "..."



async def stream_with_llm(
    four_pillars: FourPillars,
    gender: Gender,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_info: str,
    rag_context: str = "",
    category: str = "wealth",
) -> AsyncIterator[str]:
    """사주 스트리밍 분석 (category: wealth / love)."""
    user_file, system_file, prefill_file = _category_prompt_files(category)
    user_template = _load(user_file)
    system = _load(system_file)
    prefill = _load(prefill_file) if prefill_file else None

    user_message = _build_user_message(
        user_template,
        four_pillars,
        gender,
        birth_info,
        rag_context,
        birth_year,
        birth_month,
        birth_day,
    )
    messages = [{"role": "user", "content": user_message}]
    if prefill:
        messages.append({"role": "assistant", "content": prefill})

    print(f"[LLM] 스트림 요청 | model={MODEL} | prompt={len(user_message)}자 | rag={len(rag_context)}자", flush=True)

    t0 = time.perf_counter()
    ttft: float | None = None

    async with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=_cached_system(system),
        messages=messages,
    ) as stream:
        async for delta in stream.text_stream:
            if ttft is None:
                ttft = time.perf_counter() - t0
            yield delta
        try:
            final = await stream.get_final_message()
            total = time.perf_counter() - t0
            u = final.usage
            cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
            cache_write = getattr(u, "cache_creation_input_tokens", 0) or 0
            print(
                f"[LLM] 스트림 완료 | 총 {total:.2f}s (TTFT {ttft:.2f}s)"
                f" | stop={final.stop_reason}"
                f" | in={u.input_tokens} out={u.output_tokens}"
                f" | cache_read={cache_read} cache_write={cache_write}",
                flush=True,
            )
        except Exception as e:
            print(f"[LLM] get_final_message 실패: {e}")
