"""
RAG 서비스 — LangChain + ChromaDB로 사주 이론 문서를 검색해 LLM 컨텍스트를 보강합니다.
"""

import time
from pathlib import Path

import settings
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings

from schemas.saju import FourPillars
from services.ganji import stem_to_korean as _stem_to_korean, branch_to_korean as _branch_to_korean

CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
COLLECTION_NAME = "saju_theory"

_QUERY_GEN_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""당신은 사주명리학 이론 문서 검색 전문가입니다.
아래 사주 정보를 보고, 벡터DB에서 관련 문서를 찾기 위한 검색 키워드 7개를 생성하세요.

[문서 용어 목록 — 이 용어들을 키워드에 반드시 포함]
십신: 비견, 겁재, 식신, 상관, 편재, 정재, 편관, 정관, 편인, 정인
용신: 억부용신, 조후용신, 통관용신, 병약용신
格局: 정관격, 편관격, 식신격, 상관격, 편재격, 정재격, 정인격, 편인격
오행: 목, 화, 토, 금, 수
신강신약: 신강, 신약
합충: 천간합, 지지합, 육합, 삼합, 방합, 충, 형, 파, 해
십이운성: 장생, 목욕, 관대, 건록, 제왕, 쇠, 병, 사, 묘, 절, 태, 양
대운세운: 대운, 세운

[규칙]
- 위 용어를 중심으로 2~4단어 키워드 구성
- 일주·일간 정보는 용어와 조합 (예: 갑목 편재, 갑목 정관격)
- 자연어 문장 절대 금지
- 줄바꿈으로 구분, 번호·설명 없이 키워드만 출력

사주 정보:
{question}

검색 키워드:""",
)

# category별 관련 문서 카테고리 필터
_CATEGORY_FILTER: dict[str, list[str]] = {
    "wealth":     ["용신", "십신", "격국", "오행", "육친론", "신강신약", "십이운성"],
    "love":       ["십신", "육친론", "신살", "합충", "지지", "천간", "격국"],
    "fortune":    ["대운세운", "신살", "귀인", "합충", "용신", "십이운성"],
    "pastlife":   ["천간", "지지", "오행", "십이운성", "신살"],
    "vocation":   ["십신", "격국", "용신", "육친론", "오행", "신강신약"],
    "daewoon":    ["대운세운", "합충", "용신", "신강신약", "십이운성"],
    "couple":     ["합충", "형파해", "십신", "육친론", "지지", "신살"],
    "family":     ["육친론", "십신", "합충", "형파해", "귀인"],
    "friendship": ["십신", "육친론", "합충", "신살", "오행"],
}

# 싱글톤 — 앱 수명 동안 재사용
_vectorstore: Chroma | None = None
_query_chain = None  # PromptTemplate | ChatAnthropic


def _get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
        # embeddings = HuggingFaceEmbeddings(
        #     model_name="BAAI/bge-m3",  # 이 도메인에서 유사도 점수 분포가 낮아 비적합
        #     encode_kwargs={"normalize_embeddings": True},
        # )
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
            model=settings.get_llm_model(),
            api_key=settings.get_anthropic_api_key(),
            max_tokens=300,
            temperature=0,
        )
        _query_chain = _QUERY_GEN_PROMPT | llm
    return _query_chain



def _build_context_query(four_pillars: FourPillars, category: str) -> str:
    """쿼리 생성 LLM에 전달할 컨텍스트 문자열."""
    day_pillar_kr   = four_pillars.day_pillar.korean          # 예: 갑신
    day_stem_kr     = _stem_to_korean(four_pillars.day_pillar.heavenly_stem)
    month_branch_kr = _branch_to_korean(four_pillars.month_pillar.earthly_branch)
    year_branch_kr  = _branch_to_korean(four_pillars.year_pillar.earthly_branch)

    focus = {
        "wealth":     "재물운, 재성·식상·관성, 용신, 오행 균형, 재물 흐름, 대운·세운",
        "love":       "연애운, 배우자 인연, 관성·재성, 도화살, 배우자궁, 감정 패턴, 대운·세운",
        "fortune":    "대운·세운·월운, 용신 흐름, 오행 길흉, 행운, 월지 특성, 신살",
        "pastlife":   "납음오행, 공망, 원국 기질, 전생 인연, 업(業), 숙명적 특성",
        "vocation":   "직업 적성, 관성·식상·재성, 십신 특성, 용신, 전문성, 사회적 역할",
        "daewoon":    "대운 흐름, 세운, 행운(行運), 용신 변화, 운의 길흉, 천간지지 변화",
        "couple":     "일주 합충, 오행 조화, 부부궁, 배우자성, 관계 천간지지 합충, 궁합",
        "family":     "육친, 부모궁·형제궁·자녀궁, 인성·비겁, 가족 인연, 육친 합충",
        "friendship": "비겁·식상, 사회성, 인간관계, 합충, 군비, 대인관계 패턴",
    }.get(category, "성격·기질, 오행 특성, 용신, 신살·귀인")

    return (
        f"일주: {day_pillar_kr}, 일간: {day_stem_kr}, 월지: {month_branch_kr}, 연지: {year_branch_kr}\n"
        f"분석 주제: {focus}"
    )


def search_relevant_theory(
    four_pillars: FourPillars, n_results: int = 10, category: str = "wealth"
) -> str:
    """
    사주팔자에서 핵심 요소를 추출해 관련 이론 문서를 검색합니다.
    Returns: LLM 프롬프트에 삽입할 컨텍스트 문자열
    """
    vectorstore = _get_vectorstore()
    context_query = _build_context_query(four_pillars, category)
    t0 = time.perf_counter()

    # 1단계: LLM으로 명리 키워드 7개 생성
    response = _get_query_chain().invoke({"question": context_query})
    queries = [q.strip() for q in response.content.strip().splitlines() if q.strip()]
    t_query = time.perf_counter() - t0
    print(f"[RAG] 쿼리 생성 {t_query:.2f}s → {queries}", flush=True)

    # category 필터 구성
    allowed = _CATEGORY_FILTER.get(category)
    chroma_filter = {"category": {"$in": allowed}} if allowed else None

    # 2단계: 쿼리별 유사도 검색 + 중복 제거
    seen_ids: set[str] = set()
    docs_with_scores: list[tuple] = []  # (name, doc, similarity)

    for query in queries:
        # distance: 코사인 거리 (0=동일, 1=무관). similarity = 1 - distance
        results = vectorstore.similarity_search_with_score(
            query, k=5, filter=chroma_filter
        )
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
