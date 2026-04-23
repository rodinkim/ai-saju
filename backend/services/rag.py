"""
RAG 서비스 — LangChain + ChromaDB로 사주 이론 문서를 검색해 LLM 컨텍스트를 보강합니다.
"""

import os
import time
from pathlib import Path
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings

from schemas.saju import FourPillars

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "saju_theory"

_QUERY_GEN_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""당신은 사주명리학 이론 검색 전문가입니다.
아래 사주 정보를 보고, 관련 이론 문서를 찾기 위한 다양한 검색 쿼리 5개를 생성하세요.
각 쿼리는 줄바꿈으로 구분하고, 번호·설명 없이 쿼리 텍스트만 출력하세요.

사주 정보:
{question}

검색 쿼리:""",
)

# 싱글톤 — 앱 수명 동안 재사용
_vectorstore: Optional[Chroma] = None
_query_chain = None  # PromptTemplate | ChatAnthropic


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )
    return _vectorstore


def _get_query_chain():
    """쿼리 생성 체인: 프롬프트 → Haiku → 쿼리 목록"""
    global _query_chain
    if _query_chain is None:
        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=300,
            temperature=0,
        )
        _query_chain = _QUERY_GEN_PROMPT | llm
    return _query_chain


def _stem_to_korean(stem: str) -> str:
    mapping = {"甲":"갑","乙":"을","丙":"병","丁":"정","戊":"무",
               "己":"기","庚":"경","辛":"신","壬":"임","癸":"계"}
    return mapping.get(stem, stem)


def _branch_to_korean(branch: str) -> str:
    mapping = {"子":"자","丑":"축","寅":"인","卯":"묘","辰":"진","巳":"사",
               "午":"오","未":"미","申":"신","酉":"유","戌":"술","亥":"해"}
    return mapping.get(branch, branch)


def _build_context_query(four_pillars: FourPillars, category: str) -> str:
    """쿼리 생성 LLM에 전달할 컨텍스트 문자열."""
    day_stem_kr     = _stem_to_korean(four_pillars.day_pillar.heavenly_stem)
    month_branch_kr = _branch_to_korean(four_pillars.month_pillar.earthly_branch)
    year_branch_kr  = _branch_to_korean(four_pillars.year_pillar.earthly_branch)

    focus = {
        "wealth": "재물운, 직업, 재성·식상·관성, 용신, 오행 균형, 대운·세운",
        "love":   "연애운, 인연, 배우자 성향, 관성·재성, 도화살, 감정 패턴, 대운·세운",
    }.get(category, "성격·기질, 오행 특성, 용신, 신살·귀인")

    return (
        f"일간: {day_stem_kr}, 월지: {month_branch_kr}, 연지: {year_branch_kr}\n"
        f"분석 주제: {focus}"
    )


def search_relevant_theory(
    four_pillars: FourPillars, n_results: int = 7, category: str = "wealth"
) -> str:
    """
    사주팔자에서 핵심 요소를 추출해 관련 이론 문서를 검색합니다.
    Returns: LLM 프롬프트에 삽입할 컨텍스트 문자열
    """
    vectorstore = _get_vectorstore()
    context_query = _build_context_query(four_pillars, category)
    t0 = time.perf_counter()

    # 1단계: Haiku로 검색 쿼리 5개 생성
    response = _get_query_chain().invoke({"question": context_query})
    queries = [q.strip() for q in response.content.strip().splitlines() if q.strip()]
    t_query = time.perf_counter() - t0
    print(f"[RAG] 쿼리 생성 {t_query:.2f}s → {queries}", flush=True)

    # 2단계: 쿼리별 유사도 검색 + 중복 제거
    seen_ids: set[str] = set()
    docs_with_scores: list[tuple] = []  # (name, doc, similarity)

    for query in queries:
        # distance: 코사인 거리 (0=동일, 1=무관). similarity = 1 - distance
        results = vectorstore.similarity_search_with_score(query, k=3)
        for doc, distance in results:
            doc_id = doc.id or doc.metadata.get("name", doc.page_content[:30])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                name = doc.metadata.get("name", "?")
                docs_with_scores.append((name, doc, 1 - distance))

    # 유사도 내림차순 정렬 → 상위 n_results개
    docs_with_scores.sort(key=lambda x: x[2], reverse=True)
    top_docs = docs_with_scores[:n_results]

    elapsed = time.perf_counter() - t0
    print(
        f"[RAG] 총 {elapsed:.2f}s | 후보 {len(docs_with_scores)}개 → 상위 {len(top_docs)}개 채택",
        flush=True,
    )
    for name, _, score in top_docs:
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"  {bar} {score:.3f}  {name}", flush=True)

    if not top_docs:
        return ""

    lines = ["[참고 사주 이론]"]
    for _, doc, _ in top_docs:
        name = doc.metadata.get("name", "")
        lines.append(f"\n### {name}\n{doc.page_content}")

    context = "\n".join(lines)
    print(f"[RAG] 컨텍스트 길이: {len(context)}자", flush=True)
    return context
