from uuid import UUID
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.stripe.service import StripeService

router = APIRouter(tags=["stripe"])


@router.get("/integrations/stripe/connect")
async def stripe_connect(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    url = await service.initiate_connect(business_id, current_user.id)
    return {"url": url}


@router.get("/integrations/stripe/callback")
async def stripe_callback(
    code: str,
    state: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = StripeService(db)
    await service.handle_connect_callback(code, state)
    return RedirectResponse(f"http://localhost:4321/dashboard?business_id={state}")


@router.get("/integrations/stripe/status")
async def stripe_status(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StripeService(db).get_connection_status(business_id)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    await StripeService(db).handle_webhook(payload, signature)
    return {"status": "ok"}
