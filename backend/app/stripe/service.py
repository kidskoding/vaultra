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

    async def initiate_connect(self, business_id: UUID) -> str:
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "stripe",
            )
        )
        integration = result.scalar_one_or_none()
        if not integration:
            account = stripe_lib.Account.create(type="standard")
            integration = IntegrationAccount(
                business_id=business_id,
                provider="stripe",
                external_id=account["id"],
                status="pending",
                metadata_={
                    "details_submitted": account.get("details_submitted"),
                    "charges_enabled": account.get("charges_enabled"),
                    "payouts_enabled": account.get("payouts_enabled"),
                },
            )
            self.db.add(integration)
            await self.db.commit()
            await self.db.refresh(integration)

        return_url = f"{settings.BACKEND_BASE_URL}/api/v1/integrations/stripe/return?business_id={business_id}"
        refresh_url = f"{settings.FRONTEND_BASE_URL}/onboarding/stripe-connect?business_id={business_id}"
        account_link = stripe_lib.AccountLink.create(
            account=integration.external_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type="account_onboarding",
        )
        return account_link["url"]

    async def handle_account_return(self, business_id: UUID) -> IntegrationAccount:
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "stripe",
            )
        )
        integration = result.scalar_one_or_none()
        if not integration:
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Stripe integration not found"}})

        account = stripe_lib.Account.retrieve(integration.external_id)
        details_submitted = account.get("details_submitted")
        charges_enabled = account.get("charges_enabled")
        payouts_enabled = account.get("payouts_enabled")
        integration.status = "active" if details_submitted else "pending"
        integration.metadata_ = {
            "details_submitted": details_submitted,
            "charges_enabled": charges_enabled,
            "payouts_enabled": payouts_enabled,
        }
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
