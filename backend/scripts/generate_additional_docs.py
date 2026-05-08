"""
추가 RAG 문서 생성: 일주론(60), 신강신약(5), 형파해(8), 육친론(10)
사용법: python scripts/generate_additional_docs.py
"""

import json
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = anthropic.Anthropic()
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "saju_docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
BRANCHES_KR = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
STEMS_HJ = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES_HJ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def generate(prompt: str, max_tokens: int = 800) -> str:
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    time.sleep(0.5)
    return msg.content[0].text.strip()


def save(filename: str, docs: list[dict]):
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {filename} ({len(docs)}개)")


# ── 일주론 (60개) ─────────────────────────────────────────────────

def make_pillars():
    pillars = []
    for i in range(60):
        s, b = i % 10, i % 12
        pillars.append((STEMS_KR[s], BRANCHES_KR[b], STEMS_HJ[s], BRANCHES_HJ[b]))
    return pillars


def gen_ilju():
    docs = []
    pillars = make_pillars()
    for idx, (skr, bkr, shj, bhj) in enumerate(pillars, 1):
        name = f"{skr}{bkr}({shj}{bhj}) 일주"
        print(f"[{idx}/60] {name} 생성 중...")
        content = generate(
            f"사주명리학에서 {skr}{bkr}({shj}{bhj}) 일주의 특성을 300자 내외로 설명하라. "
            f"포함 내용: 오행 성질, 성격·기질, 강점과 약점, 재물·직업 경향, 배우자 인연 및 궁합 성향. "
            f"마크다운 없이 자연어 문단으로만 작성."
        )
        docs.append({
            "id": f"일주론_{skr}{bkr}",
            "category": "일주론",
            "name": name,
            "content": content,
        })
    save("일주론.json", docs)


# ── 신강신약 (5개) ────────────────────────────────────────────────

SHINGANG_ITEMS = [
    ("신강_판단법", "신강(身强) 사주 판단법과 특성"),
    ("신약_판단법", "신약(身弱) 사주 판단법과 특성"),
    ("신강_용신", "신강 사주의 용신 선택과 운용 원칙"),
    ("신약_용신", "신약 사주의 용신 선택과 운용 원칙"),
    ("종격_특수격", "종강·종약·종아·종재·종살 등 특수 종격 사주"),
]


def gen_shingang():
    docs = []
    for idx, (doc_id, topic) in enumerate(SHINGANG_ITEMS, 1):
        print(f"[{idx}/{len(SHINGANG_ITEMS)}] {topic} 생성 중...")
        content = generate(
            f"사주명리학에서 {topic}을 300자 내외로 설명하라. "
            f"판단 기준, 핵심 특성, 실전 적용 방법을 포함하라. "
            f"마크다운 없이 자연어 문단으로만 작성."
        )
        docs.append({
            "id": f"신강신약_{doc_id}",
            "category": "신강신약",
            "name": topic,
            "content": content,
        })
    save("신강신약.json", docs)


# ── 형파해 (8개) ──────────────────────────────────────────────────

HYEONG_ITEMS = [
    ("삼형_인사신", "삼형(三刑) — 인사신(寅巳申) 무은지형"),
    ("삼형_축술미", "삼형(三刑) — 축술미(丑戌未) 지세지형"),
    ("삼형_자묘", "삼형(三刑) — 자묘(子卯) 무례지형"),
    ("자형", "자형(自刑) — 진진·오오·유유·해해"),
    ("파_종류", "파(破) — 자유·오묘·인해·사신·축진·술미 여섯 가지 파"),
    ("해_종류", "해(害) — 자미·축오·인사·묘진·신해·유술 여섯 가지 해"),
    ("형파해_실전", "형파해가 사주에 있을 때 실전 해석 원칙"),
    ("형파해_운세", "형파해가 대운·세운에서 발동할 때 영향"),
]


def gen_hyeong():
    docs = []
    for idx, (doc_id, topic) in enumerate(HYEONG_ITEMS, 1):
        print(f"[{idx}/{len(HYEONG_ITEMS)}] {topic} 생성 중...")
        content = generate(
            f"사주명리학에서 {topic}을 300자 내외로 설명하라. "
            f"해당 지지 조합, 발생하는 현상, 실생활 영향을 포함하라. "
            f"마크다운 없이 자연어 문단으로만 작성."
        )
        docs.append({
            "id": f"형파해_{doc_id}",
            "category": "형파해",
            "name": topic,
            "content": content,
        })
    save("형파해.json", docs)


# ── 육친론 (10개) ─────────────────────────────────────────────────

YUKCHHIN_ITEMS = [
    ("비견", "비견(比肩) — 형제·동료·경쟁자"),
    ("겁재", "겁재(劫財) — 경쟁·손재·강한 자아"),
    ("식신", "식신(食神) — 자녀·창의·복록"),
    ("상관", "상관(傷官) — 표현력·반항·재능"),
    ("편재", "편재(偏財) — 유동재물·이성·사업"),
    ("정재", "정재(正財) — 안정재물·배우자(남)·성실"),
    ("편관", "편관(偏官) — 권력·압박·배우자(여)"),
    ("정관", "정관(正官) — 명예·규범·배우자(여)"),
    ("편인", "편인(偏印) — 편향된 학문·고독·의식주"),
    ("정인", "정인(正印) — 학문·부모·자격"),
]


def gen_yukchhin():
    docs = []
    for idx, (doc_id, topic) in enumerate(YUKCHHIN_ITEMS, 1):
        print(f"[{idx}/{len(YUKCHHIN_ITEMS)}] {topic} 생성 중...")
        content = generate(
            f"사주명리학 육친론에서 {topic}을 300자 내외로 설명하라. "
            f"포함 내용: 상징하는 육친 관계, 성격적 특성, 직업·재물 연관성, 과다·부재 시 영향. "
            f"마크다운 없이 자연어 문단으로만 작성."
        )
        docs.append({
            "id": f"육친론_{doc_id}",
            "category": "육친론",
            "name": topic,
            "content": content,
        })
    save("육친론.json", docs)


# ── 실행 ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    targets = args if args else ["ilju", "shingang", "hyeong", "yukchhin"]

    if "ilju" in targets:
        print("\n=== 일주론 (60개) ===")
        gen_ilju()
    if "shingang" in targets:
        print("\n=== 신강신약 (5개) ===")
        gen_shingang()
    if "hyeong" in targets:
        print("\n=== 형파해 (8개) ===")
        gen_hyeong()
    if "yukchhin" in targets:
        print("\n=== 육친론 (10개) ===")
        gen_yukchhin()

    print("\n완료. clean_markdown.py → load_to_chroma.py 순서로 실행하세요.")
