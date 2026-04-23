"""
ChromaDB 로드 스크립트
생성된 사주 이론 문서를 ChromaDB에 저장합니다.
임베딩 모델: jhgan/ko-sroberta-multitask (한국어 특화)
"""

import json
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

DOCS_DIR = Path(__file__).parent.parent / "data" / "saju_docs"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "saju_theory"
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"


def load_to_chroma():
    all_path = DOCS_DIR / "all.json"
    docs = json.loads(all_path.read_text(encoding="utf-8"))
    print(f"문서 로드: {len(docs)}개")

    # 기존 컬렉션 삭제
    raw_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    existing = [c.name for c in raw_client.list_collections()]
    if COLLECTION_NAME in existing:
        raw_client.delete_collection(COLLECTION_NAME)
        print(f"기존 컬렉션 '{COLLECTION_NAME}' 삭제")

    # 한국어 임베딩 모델로 새 컬렉션 생성
    print(f"임베딩 모델 로드: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    texts = [d["content"] for d in docs]
    metadatas = [{"category": d["category"], "name": d["name"]} for d in docs]
    ids = [d["id"] for d in docs]

    print("ChromaDB에 임베딩 저장 중...")
    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        ids=ids,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )

    print(f"\n총 {len(docs)}개 문서 저장 완료 → {CHROMA_DIR}")

    # 검색 테스트
    print("\n[검색 테스트] '재물운 직업 용신'")
    results = vectorstore.similarity_search_with_score("재물운 직업 용신", k=3)
    for doc, score in results:
        print(f"  {doc.metadata['name']} | 유사도 {1-score:.3f}")


if __name__ == "__main__":
    load_to_chroma()
