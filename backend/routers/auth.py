import os
import secrets

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from database import get_db
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
NAVER_REDIRECT_URI  = os.environ.get("NAVER_REDIRECT_URI", "http://localhost:8000/auth/naver/callback")
FRONTEND_URL        = os.environ.get("FRONTEND_URL", "http://localhost:5173")

KAKAO_CLIENT_ID     = os.environ.get("KAKAO_CLIENT_ID", "")
KAKAO_CLIENT_SECRET = os.environ.get("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI  = os.environ.get("KAKAO_REDIRECT_URI", "http://localhost:8000/auth/kakao/callback")

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

JWT_SECRET    = os.environ.get("JWT_SECRET_KEY", "change-this-secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE    = int(os.environ.get("JWT_EXPIRE_MINUTES", "10080"))


def _issue_jwt(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE)
    return jwt.encode({"sub": str(user_id), "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_jwt(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없음")
    return user


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return _decode_jwt(authorization.removeprefix("Bearer "), db)
    except HTTPException:
        return None


def require_current_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    return user


# ── 네이버 로그인 시작 ──────────────────────────────────────────
@router.get("/naver")
async def naver_login():
    state = secrets.token_urlsafe(16)
    url = (
        "https://nid.naver.com/oauth2.0/authorize"
        f"?response_type=code"
        f"&client_id={NAVER_CLIENT_ID}"
        f"&redirect_uri={NAVER_REDIRECT_URI}"
        f"&state={state}"
    )
    return RedirectResponse(url)


# ── 네이버 콜백 ────────────────────────────────────────────────
@router.get("/naver/callback")
async def naver_callback(
    code: str | None = None,
    state: str = "",
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}/")

    async with httpx.AsyncClient(verify=False) as client:
        token_res = await client.post(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type":    "authorization_code",
                "client_id":     NAVER_CLIENT_ID,
                "client_secret": NAVER_CLIENT_SECRET,
                "code":          code,
                "state":         state,
            },
        )
        token_data = token_res.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="네이버 토큰 발급 실패")

    async with httpx.AsyncClient(verify=False) as client:
        profile_res = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile = profile_res.json().get("response", {})

    provider_id = profile.get("id")
    if not provider_id:
        raise HTTPException(status_code=400, detail="네이버 사용자 정보 조회 실패")

    user = db.query(User).filter_by(provider="naver", provider_id=str(provider_id)).first()
    if not user:
        user = User(
            provider="naver",
            provider_id=str(provider_id),
            email=profile.get("email"),
            name=profile.get("name"),
            profile_image=profile.get("profile_image"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = _issue_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_URL}/?token={token}")


# ── 카카오 로그인 시작 ─────────────────────────────────────────
@router.get("/kakao")
async def kakao_login():
    url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
    )
    return RedirectResponse(url)


# ── 카카오 콜백 ────────────────────────────────────────────────
@router.get("/kakao/callback")
async def kakao_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}/")

    async with httpx.AsyncClient(verify=False) as client:
        token_res = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type":   "authorization_code",
                "client_id":    KAKAO_CLIENT_ID,
                "redirect_uri": KAKAO_REDIRECT_URI,
                "code":         code,
                **({"client_secret": KAKAO_CLIENT_SECRET} if KAKAO_CLIENT_SECRET else {}),
            },
        )
        token_data = token_res.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패")

    async with httpx.AsyncClient(verify=False) as client:
        profile_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile = profile_res.json()

    provider_id = profile.get("id")
    if not provider_id:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")

    kakao_account = profile.get("kakao_account", {})
    kakao_profile = kakao_account.get("profile", {})

    user = db.query(User).filter_by(provider="kakao", provider_id=str(provider_id)).first()
    if not user:
        user = User(
            provider="kakao",
            provider_id=str(provider_id),
            email=kakao_account.get("email"),
            name=kakao_profile.get("nickname"),
            profile_image=kakao_profile.get("profile_image_url"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = _issue_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_URL}/?token={token}")


# ── 구글 로그인 시작 ───────────────────────────────────────────
@router.get("/google")
async def google_login():
    state = secrets.token_urlsafe(16)
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
        f"&state={state}"
    )
    return RedirectResponse(url)


# ── 구글 콜백 ──────────────────────────────────────────────────
@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str = "",
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}/")

    async with httpx.AsyncClient(verify=False) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type":    "authorization_code",
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  GOOGLE_REDIRECT_URI,
                "code":          code,
            },
        )
        token_data = token_res.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="구글 토큰 발급 실패")

    async with httpx.AsyncClient(verify=False) as client:
        profile_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile = profile_res.json()

    provider_id = profile.get("id")
    if not provider_id:
        raise HTTPException(status_code=400, detail="구글 사용자 정보 조회 실패")

    user = db.query(User).filter_by(provider="google", provider_id=str(provider_id)).first()
    if not user:
        user = User(
            provider="google",
            provider_id=str(provider_id),
            email=profile.get("email"),
            name=profile.get("name"),
            profile_image=profile.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = _issue_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_URL}/?token={token}")


# ── 내 정보 조회 ───────────────────────────────────────────────
@router.get("/me")
async def me(authorization: str = Header(...), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer 토큰 필요")
    token = authorization.removeprefix("Bearer ")
    user = _decode_jwt(token, db)
    return {
        "id":            user.id,
        "provider":      user.provider,
        "name":          user.name,
        "email":         user.email,
        "profile_image": user.profile_image,
        "credits":       user.credits,
    }
