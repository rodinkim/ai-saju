import settings  # noqa: F401 — load backend/.env before other modules read os.environ

from fastapi import FastAPI
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
from routers import saju, auth, payment
from services.llm import MODEL
from database import engine, Base
from sqlalchemy import text
import models.user     # noqa: F401
import models.payment  # noqa: F401

app = FastAPI(
    title="토정 API",
    description="AI 명리 분석 서비스",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev: allow localhost/LAN frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(saju.router)
app.include_router(auth.router)
app.include_router(payment.router)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS credits INTEGER NOT NULL DEFAULT 100"
        ))
        conn.execute(text("UPDATE users SET credits = 100 WHERE credits = 1"))
        conn.commit()
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
