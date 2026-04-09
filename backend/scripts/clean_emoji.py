"""기존 saju_docs JSON 파일에서 이모티콘 제거"""

import json
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "data" / "saju_docs"

EMOJI_PATTERN = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F300-\U0001F9FF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def remove_emoji(text: str) -> str:
    return EMOJI_PATTERN.sub("", text).strip()


def clean_file(path: Path):
    docs = json.loads(path.read_text(encoding="utf-8"))
    for doc in docs:
        doc["content"] = remove_emoji(doc["content"])
    path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"정리 완료: {path.name}")


for f in DOCS_DIR.glob("*.json"):
    clean_file(f)
