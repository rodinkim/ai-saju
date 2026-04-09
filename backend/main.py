from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import saju
from services.llm import FREE_MODEL, PAID_MODEL

app = FastAPI(
    title="AI 사주 분석 서비스",
    description="LangGraph + CrewAI 기반 사주 분석 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React Vite 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(saju.router)


@app.on_event("startup")
async def startup():
    print(f"\n{'='*50}")
    print(f"  AI 사주 분석 서비스 시작 v2")
    print(f"  무료 모델: {FREE_MODEL}")
    print(f"  유료 모델: {PAID_MODEL}")
    print(f"{'='*50}\n")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "AI 사주 분석 서비스 API"}
