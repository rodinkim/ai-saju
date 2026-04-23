import settings  # noqa: F401 — load backend/.env before other modules read os.environ

from fastapi import FastAPI
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from routers import saju
from services.llm import MODEL

app = FastAPI(
    title="AI 사주 분석 서비스",
    description="LangGraph + CrewAI 기반 사주 분석 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev: allow localhost/LAN frontend origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(saju.router)


@app.on_event("startup")
async def startup():
    print(f"\n{'='*50}")
    print(f"  AI 사주 분석 서비스 시작 v2")
    print(f"  모델: {MODEL}")
    print(f"{'='*50}\n")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_well_known():
    return Response(status_code=204)


@app.get("/")
async def root():
    return {"message": "AI 사주 분석 서비스 API"}
