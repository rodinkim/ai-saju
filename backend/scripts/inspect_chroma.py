"""
ChromaDB 저장 내용 조회 스크립트
사용법:
  python scripts/inspect_chroma.py            # 전체 통계
  python scripts/inspect_chroma.py 오행       # 카테고리별 조회
  python scripts/inspect_chroma.py search 직업  # 검색
"""

import sys
from pathlib import Path

import chromadb

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "saju_theory"

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


def show_stats(col):
    total = col.count()
    print(f"컬렉션: {COLLECTION_NAME}")
    print(f"총 문서 수: {total}개\n")

    all_docs = col.get(include=["metadatas"])
    categories = {}
    for meta in all_docs["metadatas"]:
        cat = meta["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print("카테고리별:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}개")


def show_category(col, category):
    results = col.get(where={"category": category}, include=["metadatas", "documents"])
    if not results["ids"]:
        print(f"'{category}' 카테고리를 찾을 수 없습니다.")
        return

    print(f"[{category}] {len(results['ids'])}개\n")
    for doc_id, meta, doc in zip(results["ids"], results["metadatas"], results["documents"]):
        print(f"▶ {meta['name']} (id: {doc_id})")
        print(f"{doc[:200].strip()}")
        print("-" * 60)


def search(col, query):
    results = col.query(query_texts=[query], n_results=5)
    print(f"검색어: '{query}'\n")
    for i, (doc_id, meta, doc, dist) in enumerate(zip(
        results["ids"][0],
        results["metadatas"][0],
        results["documents"][0],
        results["distances"][0],
    ), 1):
        print(f"{i}. [{meta['category']}] {meta['name']}  (유사도: {1 - dist:.3f})")
        print(f"   {doc[:150].strip()}...")
        print()


def main():
    col = get_collection()
    args = sys.argv[1:]

    if not args:
        show_stats(col)
    elif args[0] == "search" and len(args) > 1:
        search(col, " ".join(args[1:]))
    else:
        show_category(col, args[0])


if __name__ == "__main__":
    main()
