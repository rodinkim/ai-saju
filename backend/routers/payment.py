import os
import base64

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.payment import Payment
from models.user import User
from routers.auth import require_current_user

router = APIRouter(prefix="/payment", tags=["결제"])

TOSS_SECRET_KEY = os.environ.get("TOSS_SECRET_KEY", "")

CREDIT_PACKAGES = {
    4900:  100,
    12900: 300,
    19900: 500,
}


class ConfirmRequest(BaseModel):
    paymentKey: str
    orderId: str
    amount: int


@router.post("/confirm")
async def confirm_payment(
    req: ConfirmRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    # 중복 결제 방지
    if db.query(Payment).filter_by(order_id=req.orderId).first():
        raise HTTPException(status_code=400, detail="이미 처리된 주문입니다")

    # 금액 유효성 확인
    credits = CREDIT_PACKAGES.get(req.amount)
    if not credits:
        raise HTTPException(status_code=400, detail="유효하지 않은 결제 금액입니다")

    # 토스 결제 승인
    secret = base64.b64encode(f"{TOSS_SECRET_KEY}:".encode()).decode()
    async with httpx.AsyncClient(verify=False) as client:
        res = await client.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            headers={
                "Authorization": f"Basic {secret}",
                "Content-Type": "application/json",
            },
            json={
                "paymentKey": req.paymentKey,
                "orderId":    req.orderId,
                "amount":     req.amount,
            },
        )

    if res.status_code != 200:
        err = res.json()
        raise HTTPException(status_code=400, detail=err.get("message", "결제 승인 실패"))

    # 결제 내역 저장 + 크레딧 지급
    db.add(Payment(
        user_id=current_user.id,
        order_id=req.orderId,
        payment_key=req.paymentKey,
        amount=req.amount,
        credits=credits,
    ))
    current_user.credits += credits
    db.commit()

    return {"credits": current_user.credits, "added": credits}
