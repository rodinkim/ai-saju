"""기존 saju_docs JSON 파일에서 마크다운 기호 제거"""

import json
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "data" / "saju_docs"

_HANJA_RE = re.compile(r'\([一-鿿㐀-䶿·]+\)')  # (偏官) 같은 한자 괄호


def strip_markdown(text: str) -> str:
    text = re.sub(r'#{1,6}\s*', '', text)                        # ## 헤더
    text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)          # **bold**, *italic*
    text = re.sub(r'`{1,3}(.+?)`{1,3}', r'\1', text)            # `코드`
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)   # 목록 기호
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)   # 번호 목록
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)              # [링크](url)
    text = re.sub(r'^\|[-| :]+\|$', '', text, flags=re.MULTILINE)  # 테이블 구분선 |---|---|
    text = re.sub(r'^\|.+\|$', '', text, flags=re.MULTILINE)    # 테이블 행 |col|col|
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)        # 인용구 >
    text = re.sub(r'\s*\|\s*', ' ', text)                        # 인라인 | 구분자 → 공백
    text = _HANJA_RE.sub('', text)                               # (偏官) 같은 한자 괄호 제거
    text = re.sub(r'\n+', ' ', text)                             # 모든 개행 → 공백
    text = re.sub(r' {2,}', ' ', text)                           # 연속 공백 정리
    return text.strip()


def clean_file(path: Path):
    docs = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for doc in docs:
        original = doc["content"]
        cleaned = strip_markdown(original)
        if cleaned != original:
            doc["content"] = cleaned
            changed += 1
    path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"정리 완료: {path.name} ({changed}/{len(docs)}개 변경)")


for f in sorted(DOCS_DIR.glob("*.json")):
    clean_file(f)
