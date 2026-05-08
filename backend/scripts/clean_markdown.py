"""saju_docs JSON 파일에서 마크다운 기호 및 한자 제거"""

import json
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "data" / "saju_docs"

# 사주에서 자주 쓰이는 한자 → 한글 매핑
HANJA_MAP = {
    # 천간
    '甲': '갑', '乙': '을', '丙': '병', '丁': '정', '戊': '무',
    '己': '기', '庚': '경', '辛': '신', '壬': '임', '癸': '계',
    # 지지
    '子': '자', '丑': '축', '寅': '인', '卯': '묘', '辰': '진',
    '巳': '사', '午': '오', '未': '미', '申': '신', '酉': '유',
    '戌': '술', '亥': '해',
    # 오행
    '木': '목', '火': '화', '土': '토', '金': '금', '水': '수',
    # 음양
    '陰': '음', '陽': '양',
    # 기타
    '囚': '수',   # 休囚 표현
    '月': '월',   # 동지月 등
}

_HANJA_CHARS = re.compile(r'[一-鿿㐀-䶿]')

# 한자+ 뒤에 (한글만) 패턴 → 괄호 안 한글만 남김. 예: 甲(갑) → 갑, 壬(임) → 임
_HANJA_BEFORE_PAREN = re.compile(r'[一-鿿㐀-䶿]+\(([가-힣·\s]+)\)')

# (한자/구두점만) 패턴 → 통째 제거. 예: (甲子), (偏官格, 七殺格), (身强)
_HANJA_ONLY_PAREN = re.compile(r'\([一-鿿㐀-䶿·,\s]+\)')


def strip_hanja(text: str) -> str:
    # 1단계: 한자(한글) → 한글 (한자가 먼저 오는 경우)
    text = _HANJA_BEFORE_PAREN.sub(lambda m: m.group(1), text)
    # 2단계: (한자만 있는 괄호) → 제거
    text = _HANJA_ONLY_PAREN.sub('', text)
    # 3단계: 남은 독립 한자 → 매핑 변환, 미등록 한자는 제거
    text = _HANJA_CHARS.sub(lambda m: HANJA_MAP.get(m.group(), ''), text)
    # 연속 공백 정리
    text = re.sub(r' {2,}', ' ', text).strip()
    return text


def strip_markdown(text: str) -> str:
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
    text = re.sub(r'`{1,3}(.+?)`{1,3}', r'\1', text)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'^\|[-| :]+\|$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\|.+\|$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*\|\s*', ' ', text)
    text = strip_hanja(text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def clean_file(path: Path):
    docs = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for doc in docs:
        orig_id = doc.get("id", "")
        orig_name = doc.get("name", "")
        orig_content = doc.get("content", "")

        new_id = strip_hanja(orig_id)
        new_name = strip_hanja(orig_name)
        new_content = strip_markdown(orig_content)

        if new_id != orig_id or new_name != orig_name or new_content != orig_content:
            doc["id"] = new_id
            doc["name"] = new_name
            doc["content"] = new_content
            changed += 1

    path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"정리 완료: {path.name} ({changed}/{len(docs)}개 변경)")


for f in sorted(DOCS_DIR.glob("*.json")):
    clean_file(f)
