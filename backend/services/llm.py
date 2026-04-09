import os
import re
from datetime import date
from pathlib import Path
from typing import AsyncIterator
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from schemas.saju import FourPillars, Gender

load_dotenv()

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

FREE_MODEL = "claude-haiku-4-5-20251001"

def _load(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _build_user_message(template: str, fp: FourPillars, gender: Gender, birth_info: str, rag_context: str) -> str:
    return template.format(
        birth_info=birth_info,
        gender="남성" if gender == Gender.male else "여성",
        current_year=date.today().year,
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
    birth_info: str,
    rag_context: str = "",
    category: str = "free",
) -> tuple[str, str]:
    """사주 분석. Returns: (analysis, summary)"""
    user_prompt = "analyze_user.txt"
    system_prompt = "system.txt"
    if category == "wealth":
        user_prompt = "wealth_analyze_user.txt"
        system_prompt = "wealth_system.txt"

    user_message = _build_user_message(
        _load(user_prompt), four_pillars, gender, birth_info, rag_context
    )
    message = await client.messages.create(
        model=FREE_MODEL,
        max_tokens=4096,
        system=_load(system_prompt),
        messages=[{"role": "user", "content": user_message}],
    )
    return _parse_analysis(message.content[0].text)


async def stream_with_llm(
    four_pillars: FourPillars,
    gender: Gender,
    birth_info: str,
    rag_context: str = "",
    free: bool = False,
    category: str = "free",
) -> AsyncIterator[str]:
    """
    사주 스트리밍 분석.
    free=True  → 무료사주 프롬프트 + Haiku
    free=False → 일반/재물 프롬프트 + Haiku
    """
    if free:
        system = _load("free_system.txt")
        user_message = _build_user_message(
            _load("free_analyze_user.txt"), four_pillars, gender, birth_info, rag_context
        )
        model = FREE_MODEL
        max_tokens = 4096
    elif category == "wealth":
        system = _load("wealth_system.txt")
        user_message = _build_user_message(
            _load("wealth_analyze_user.txt"), four_pillars, gender, birth_info, rag_context
        )
        model = FREE_MODEL
        max_tokens = 4096
    else:
        system = _load("system.txt")
        user_message = _build_user_message(
            _load("analyze_user.txt"), four_pillars, gender, birth_info, rag_context
        )
        model = FREE_MODEL
        max_tokens = 4096

    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for delta in stream.text_stream:
            yield delta
        try:
            final = await stream.get_final_message()
            print(f"[LLM] model={model} | stop={final.stop_reason} | in={final.usage.input_tokens} out={final.usage.output_tokens} tokens")
        except Exception as e:
            print(f"[LLM] get_final_message 실패: {e}")
