"""
RAG 서비스 — ChromaDB에서 사주 이론 문서를 검색해 LLM 컨텍스트를 보강합니다.
"""

from pathlib import Path
from typing import Optional
import chromadb
from schemas.saju import FourPillars

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "saju_theory"

# 싱글톤 클라이언트 (앱 수명 동안 재사용)
_client: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_collection(COLLECTION_NAME)
    return _collection


def _stem_to_korean(stem: str) -> str:
    mapping = {"甲":"갑","乙":"을","丙":"병","丁":"정","戊":"무",
               "己":"기","庚":"경","辛":"신","壬":"임","癸":"계"}
    return mapping.get(stem, stem)


def _branch_to_korean(branch: str) -> str:
    mapping = {"子":"자","丑":"축","寅":"인","卯":"묘","辰":"진","巳":"사",
               "午":"오","未":"미","申":"신","酉":"유","戌":"술","亥":"해"}
    return mapping.get(branch, branch)


def search_relevant_theory(four_pillars: FourPillars, n_results: int = 5) -> str:
    """
    사주팔자에서 핵심 요소를 추출해 관련 이론 문서를 검색합니다.
    Returns: LLM 프롬프트에 삽입할 컨텍스트 문자열
    """
    collection = _get_collection()

    day_stem_kr = _stem_to_korean(four_pillars.day_pillar.heavenly_stem)
    month_branch_kr = _branch_to_korean(four_pillars.month_pillar.earthly_branch)
    year_branch_kr = _branch_to_korean(four_pillars.year_pillar.earthly_branch)

    queries = [
        f"{day_stem_kr} 일간 성격 특성 오행",
        f"{month_branch_kr} 월지 계절 특성",
        f"십신 용신 오행 균형 재물 직업",
        f"{year_branch_kr} 지지 특성",
        f"{day_stem_kr} 일간 천을귀인 문창귀인 암록귀인",
        f"{year_branch_kr} 역마살 도화살 화개살 신살 길흉",
    ]

    seen_ids: set[str] = set()
    docs: list[tuple[str, str, float]] = []  # (name, content, score)

    for query in queries:
        results = collection.query(query_texts=[query], n_results=3)
        for doc_id, meta, doc, dist in zip(
            results["ids"][0],
            results["metadatas"][0],
            results["documents"][0],
            results["distances"][0],
        ):
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                docs.append((meta["name"], doc, 1 - dist))

    # 유사도 상위 n_results개만 사용
    docs.sort(key=lambda x: x[2], reverse=True)
    top_docs = docs[:n_results]

    if not top_docs:
        return ""

    lines = ["[참고 사주 이론]"]
    for name, content, _ in top_docs:
        lines.append(f"\n### {name}\n{content}")

    return "\n".join(lines)
