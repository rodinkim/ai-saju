"""
ChromaDB 로드 스크립트
생성된 사주 이론 문서를 ChromaDB에 저장합니다.
"""

import json
import sys
from pathlib import Path

# Windows 터미널 인코딩 문제 방지
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chromadb

DOCS_DIR = Path(__file__).parent.parent / "data" / "saju_docs"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "saju_theory"


def load_to_chroma():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 기존 컬렉션 초기화 (재실행 시 중복 방지)
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 컬렉션 '{COLLECTION_NAME}' 삭제")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_path = DOCS_DIR / "all.json"
    docs = json.loads(all_path.read_text(encoding="utf-8"))

    ids = [d["id"] for d in docs]
    documents = [d["content"] for d in docs]
    metadatas = [{"category": d["category"], "name": d["name"]} for d in docs]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"총 {len(docs)}개 문서 저장 완료 → {CHROMA_DIR}")

    # 간단한 검색 테스트
    print("\n[검색 테스트] '재물운 직업'")
    results = collection.query(query_texts=["재물운 직업"], n_results=3)
    for i, (doc_id, doc) in enumerate(zip(results["ids"][0], results["documents"][0]), 1):
        preview = doc[:80].strip()
        print(f"  {i}. {doc_id}")
        print(f"     {preview}...")


if __name__ == "__main__":
    load_to_chroma()
