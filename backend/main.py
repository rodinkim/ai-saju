import settings  # noqa: F401 — load backend/.env before other modules read os.environ
import truststore; truststore.inject_into_ssl()  # noqa: E702 — Windows 시스템 인증서 연결

from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from routers import saju, auth, payment
from services.llm import MODEL
from database import engine, Base
import models.user     # noqa: F401
import models.payment  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print(f"\n{'='*50}")
    print(f"  AI 사주 분석 서비스 시작 v2")
    print(f"  모델: {MODEL}")
    print(f"{'='*50}\n")
    yield


app = FastAPI(
    title="토정 API",
    description="AI 명리 분석 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "https://to-jung.com",
    "https://www.to-jung.com",
    "https://saju-494604.web.app",
    "https://saju-494604.firebaseapp.com",
    "http://localhost",
    "http://192.168.100.188",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(saju.router)
app.include_router(auth.router)
app.include_router(payment.router)


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
