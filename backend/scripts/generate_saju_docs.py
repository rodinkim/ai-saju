"""
사주 이론 문서 생성 스크립트
Claude API를 사용해 RAG용 사주 이론 문서를 생성하고 JSON으로 저장합니다.
"""

import json
import time
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

client = anthropic.Anthropic()
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "saju_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 생성 대상 정의 ──────────────────────────────────────────────

OHAENG = ["목(木)", "화(火)", "토(土)", "금(金)", "수(水)"]

CHEONGAN = ["갑(甲)", "을(乙)", "병(丙)", "정(丁)", "무(戊)",
            "기(己)", "경(庚)", "신(辛)", "임(壬)", "계(癸)"]

JIJI = ["자(子)", "축(丑)", "인(寅)", "묘(卯)", "진(辰)", "사(巳)",
        "오(午)", "미(未)", "신(申)", "유(酉)", "술(戌)", "해(亥)"]

SIPSIN = ["비견(比肩)", "겁재(劫財)", "식신(食神)", "상관(傷官)",
          "편재(偏財)", "정재(正財)", "편관(偏官)", "정관(正官)",
          "편인(偏印)", "정인(正印)"]

UNSUNG = ["장생(長生)", "목욕(沐浴)", "관대(冠帶)", "건록(建祿)",
          "제왕(帝旺)", "쇠(衰)", "병(病)", "사(死)",
          "묘(墓)", "절(絶)", "태(胎)", "양(養)"]

# ── 프롬프트 템플릿 ─────────────────────────────────────────────

PROMPTS = {
    "오행": lambda name: f"""명리학에서 오행 중 {name}에 대해 설명해줘.
다음 항목을 포함해서 300자 내외로 작성해줘:
- 기본 성질과 상징
- 계절, 방위, 색깔, 신체 부위
- 성격적 특성
- 직업 적성
- 균형이 깨졌을 때의 특징

핵심 내용만 간결하게 작성해줘. 이모티콘은 사용하지 마.""",

    "천간": lambda name: f"""명리학에서 십천간 중 {name}에 대해 설명해줘.
다음 항목을 포함해서 300자 내외로 작성해줘:
- 오행 속성과 음양
- 기본 성질과 상징 (자연물에 비유)
- 성격적 특성
- 직업 적성
- 타 천간과의 관계 (합, 충)

핵심 내용만 간결하게 작성해줘. 이모티콘은 사용하지 마.""",

    "지지": lambda name: f"""명리학에서 십이지지 중 {name}에 대해 설명해줘.
다음 항목을 포함해서 300자 내외로 작성해줘:
- 오행 속성, 음양, 해당 월/시간
- 지장간 구성
- 성격적 특성
- 합충형파해 관계

핵심 내용만 간결하게 작성해줘. 이모티콘은 사용하지 마.""",

    "십신": lambda name: f"""명리학에서 십신 중 {name}에 대해 설명해줘.
다음 항목을 포함해서 300자 내외로 작성해줘:
- 일간과의 관계 (어떤 오행인지)
- 의미하는 육친 (가족관계)
- 성격과 특성
- 긍정적/부정적 작용
- 직업, 재물, 건강과의 연관

핵심 내용만 간결하게 작성해줘. 이모티콘은 사용하지 마.""",

    "십이운성": lambda name: f"""명리학에서 십이운성 중 {name}에 대해 설명해줘.
다음 항목을 포함해서 200자 내외로 작성해줘:
- 생명 주기에서의 단계 (어떤 상태인지)
- 에너지 강도 (강/중/약)
- 성격과 운세에 미치는 영향
- 일주에 있을 때의 의미

핵심 내용만 간결하게 작성해줘. 이모티콘은 사용하지 마.""",
}

# ── 생성 함수 ───────────────────────────────────────────────────

def generate_doc(category: str, name: str) -> dict:
    prompt = PROMPTS[category](name)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    content = message.content[0].text.strip()
    return {
        "id": f"{category}_{name}",
        "category": category,
        "name": name,
        "content": content,
    }


def generate_category(category: str, items: list[str], delay: float = 0.5):
    print(f"\n[{category}] 생성 시작 ({len(items)}개)")
    results = []
    for i, name in enumerate(items, 1):
        print(f"  {i}/{len(items)} {name} ...", end=" ", flush=True)
        try:
            doc = generate_doc(category, name)
            results.append(doc)
            print("완료")
        except Exception as e:
            print(f"실패: {e}")
        if i < len(items):
            time.sleep(delay)

    output_path = OUTPUT_DIR / f"{category}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  저장: {output_path}")
    return results


# ── 실행 ────────────────────────────────────────────────────────

CATEGORIES = {
    "오행": OHAENG,
    "천간": CHEONGAN,
    "지지": JIJI,
    "십신": SIPSIN,
    "십이운성": UNSUNG,
}


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target == "all":
        targets = CATEGORIES
    elif target in CATEGORIES:
        targets = {target: CATEGORIES[target]}
    else:
        print(f"사용법: python generate_saju_docs.py [all|오행|천간|지지|십신|십이운성]")
        sys.exit(1)

    total = sum(len(v) for v in targets.values())
    print(f"총 {total}개 문서 생성 시작")

    all_docs = []
    for category, items in targets.items():
        docs = generate_category(category, items)
        all_docs.extend(docs)

    if target == "all":
        combined_path = OUTPUT_DIR / "all.json"
        with open(combined_path, "w", encoding="utf-8") as f:
            json.dump(all_docs, f, ensure_ascii=False, indent=2)
        print(f"\n전체 저장: {combined_path}")

    print(f"\n완료: 총 {len(all_docs)}개 문서 생성됨")


if __name__ == "__main__":
    main()
