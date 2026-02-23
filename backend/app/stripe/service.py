from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
import stripe as stripe_lib
from app.shared.models import IntegrationAccount, StripeEvent
from app.config import settings

stripe_lib.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initiate_connect(self, business_id: UUID, user_id: UUID) -> str:
        redirect_uri = f"http://localhost:8000/api/v1/integrations/stripe/callback"
        url = (
            f"https://connect.stripe.com/oauth/authorize"
            f"?response_type=code"
            f"&client_id={settings.STRIPE_CONNECT_CLIENT_ID}"
            f"&scope=read_write"
            f"&redirect_uri={redirect_uri}"
            f"&state={business_id}"
        )
        return url

    async def handle_connect_callback(self, code: str, business_id: UUID) -> IntegrationAccount:
        try:
            response = stripe_lib.OAuth.token(grant_type="authorization_code", code=code)
        except stripe_lib.oauth_error.OAuthError as e:
            raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": str(e)}})
        account_id = response["stripe_user_id"]
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "stripe",
            )
        )
        integration = result.scalar_one_or_none()
        if integration:
            integration.external_id = account_id
            integration.status = "active"
        else:
            integration = IntegrationAccount(
                business_id=business_id,
                provider="stripe",
                external_id=account_id,
                status="active",
            )
            self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def get_connection_status(self, business_id: UUID) -> dict:
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "stripe",
            )
        )
        integration = result.scalar_one_or_none()
        if not integration or integration.status != "active":
            return {"connected": False}
        return {
            "connected": True,
            "account_id": integration.external_id,
            "last_synced_at": integration.last_synced_at,
        }

    async def handle_webhook(self, payload: bytes, signature: str) -> None:
        try:
            event = stripe_lib.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
        except (stripe_lib.error.SignatureVerificationError, ValueError) as e:
            raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid webhook signature"}})
        result = await self.db.execute(
            select(StripeEvent).where(StripeEvent.stripe_event_id == event["id"])
        )
        if result.scalar_one_or_none():
            return
        stripe_event = StripeEvent(
            stripe_event_id=event["id"],
            event_type=event["type"],
            payload={"type": event["type"], "id": event["id"]},
        )
        self.db.add(stripe_event)
        await self.db.commit()

    async def sync_account_data(self, account_id: str, business_id: UUID) -> None:
        pass
