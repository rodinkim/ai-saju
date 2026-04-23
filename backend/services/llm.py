import os
import re
import time
from datetime import date
from pathlib import Path
from typing import AsyncIterator
from anthropic import AsyncAnthropic

import settings
from schemas.saju import FourPillars, Gender

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

MODEL = settings.get_llm_model()
MAX_TOKENS = 6000

def _load(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _category_prompt_files(category: str) -> tuple[str, str]:
    if category == "love":
        return "love_analyze_user.txt", "love_system.txt"
    return "wealth_analyze_user.txt", "wealth_system.txt"


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
        reference_date_iso=ref.isoformat(),
        age_international=_international_age(birth_year, birth_month, birth_day, ref),
        age_korean=_year_counting_age(birth_year, ref),
        year_korean=fp.year_pillar.korean,   year_stem=fp.year_pillar.heavenly_stem,   year_branch=fp.year_pillar.earthly_branch,
        month_korean=fp.month_pillar.korean, month_stem=fp.month_pillar.heavenly_stem, month_branch=fp.month_pillar.earthly_branch,
        day_korean=fp.day_pillar.korean,     day_stem=fp.day_pillar.heavenly_stem,     day_branch=fp.day_pillar.earthly_branch,
        hour_korean=fp.hour_pillar.korean,   hour_stem=fp.hour_pillar.heavenly_stem,   hour_branch=fp.hour_pillar.earthly_branch,
        rag_context=rag_context,
    )


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


async def analyze_with_llm(
    four_pillars: FourPillars,
    gender: Gender,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_info: str,
    rag_context: str = "",
    category: str = "wealth",
) -> tuple[str, str]:
    """사주 분석. Returns: (analysis, summary)"""
    user_prompt, system_prompt = _category_prompt_files(category)
    user_template = _load(user_prompt)
    system_text = _load(system_prompt)

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
    print(f"[LLM] 요청 | model={MODEL} | prompt={len(user_message)}자 | rag={len(rag_context)}자", flush=True)

    t0 = time.perf_counter()
    message = await client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_text,
        messages=[{"role": "user", "content": user_message}],
    )
    elapsed = time.perf_counter() - t0
    print(
        f"[LLM] 완료 | {elapsed:.2f}s | stop={message.stop_reason}"
        f" | in={message.usage.input_tokens} out={message.usage.output_tokens} tokens",
        flush=True,
    )
    return _parse_analysis(message.content[0].text)


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
    user_file, system_file = _category_prompt_files(category)
    user_template = _load(user_file)
    system = _load(system_file)

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
    print(f"[LLM] 스트림 요청 | model={MODEL} | prompt={len(user_message)}자 | rag={len(rag_context)}자", flush=True)

    t0 = time.perf_counter()
    ttft: float | None = None

    async with client.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for delta in stream.text_stream:
            if ttft is None:
                ttft = time.perf_counter() - t0
            yield delta
        try:
            final = await stream.get_final_message()
            total = time.perf_counter() - t0
            print(
                f"[LLM] 스트림 완료 | 총 {total:.2f}s (TTFT {ttft:.2f}s)"
                f" | stop={final.stop_reason}"
                f" | in={final.usage.input_tokens} out={final.usage.output_tokens} tokens",
                flush=True,
            )
        except Exception as e:
            print(f"[LLM] get_final_message 실패: {e}")
