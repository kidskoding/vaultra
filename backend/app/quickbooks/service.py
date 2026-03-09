from uuid import UUID
import secrets
import httpx
from urllib.parse import urlencode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.shared.models import IntegrationAccount, Business
from app.config import settings

QUICKBOOKS_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QUICKBOOKS_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QUICKBOOKS_REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
QUICKBOOKS_API_BASE = {
    "sandbox": "https://sandbox-quickbooks.api.intuit.com",
    "production": "https://quickbooks.api.intuit.com",
}


class QuickBooksService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_api_base(self) -> str:
        return QUICKBOOKS_API_BASE.get(settings.QUICKBOOKS_ENVIRONMENT, QUICKBOOKS_API_BASE["sandbox"])

    async def initiate_connect(self, business_id: UUID) -> str:
        """Generate OAuth URL for QuickBooks connection."""
        # Check if business exists, create mock one in dev mode if not
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()

        if not business and (not settings.QUICKBOOKS_CLIENT_ID or settings.DEV_MODE):
            business = Business(
                id=business_id,
                name="Test Business",
                industry="technology",
            )
            self.db.add(business)
            await self.db.commit()

        # Check existing integration
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "quickbooks",
            )
        )
        integration = result.scalar_one_or_none()

        # Dev mode: create fake connection
        if not settings.QUICKBOOKS_CLIENT_ID or settings.DEV_MODE:
            if not integration:
                fake_realm_id = f"realm_test_{business_id.hex[:16]}"
                integration = IntegrationAccount(
                    business_id=business_id,
                    provider="quickbooks",
                    external_id=fake_realm_id,
                    status="active",
                    metadata_={
                        "company_name": "Test Company",
                        "environment": "sandbox",
                    },
                )
                self.db.add(integration)
                await self.db.commit()
                await self.db.refresh(integration)
            return f"{settings.FRONTEND_BASE_URL}/onboarding/quickbooks-success?business_id={business_id}"

        # Generate state token for CSRF protection (store business_id)
        state = str(business_id)

        # Build OAuth URL
        params = {
            "client_id": settings.QUICKBOOKS_CLIENT_ID,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "redirect_uri": settings.QUICKBOOKS_REDIRECT_URI,
            "state": state,
        }
        return f"{QUICKBOOKS_AUTH_URL}?{urlencode(params)}"

    async def handle_oauth_callback(
        self, code: str, state: str, realm_id: str
    ) -> IntegrationAccount:
        """Exchange authorization code for tokens and store integration."""
        business_id = UUID(state)

        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                QUICKBOOKS_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.QUICKBOOKS_REDIRECT_URI,
                },
                auth=(settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET),
                headers={"Accept": "application/json"},
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "OAUTH_ERROR",
                        "message": f"Failed to exchange code: {response.text}",
                    }
                },
            )

        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        # Get company info
        company_name = await self._get_company_name(access_token, realm_id)

        # Check for existing integration
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "quickbooks",
            )
        )
        integration = result.scalar_one_or_none()

        if integration:
            integration.external_id = realm_id
            integration.access_token_encrypted = access_token  # TODO: encrypt
            integration.status = "active"
            integration.metadata_ = {
                "refresh_token": refresh_token,  # TODO: encrypt
                "expires_in": expires_in,
                "company_name": company_name,
                "environment": settings.QUICKBOOKS_ENVIRONMENT,
            }
        else:
            integration = IntegrationAccount(
                business_id=business_id,
                provider="quickbooks",
                external_id=realm_id,
                access_token_encrypted=access_token,  # TODO: encrypt
                status="active",
                metadata_={
                    "refresh_token": refresh_token,  # TODO: encrypt
                    "expires_in": expires_in,
                    "company_name": company_name,
                    "environment": settings.QUICKBOOKS_ENVIRONMENT,
                },
            )
            self.db.add(integration)

        await self.db.commit()
        await self.db.refresh(integration)
        return integration

    async def _get_company_name(self, access_token: str, realm_id: str) -> str:
        """Fetch company name from QuickBooks."""
        api_base = self._get_api_base()
        url = f"{api_base}/v3/company/{realm_id}/companyinfo/{realm_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )

        if response.status_code == 200:
            data = response.json()
            return data.get("CompanyInfo", {}).get("CompanyName", "Unknown")
        return "Unknown"

    async def refresh_access_token(self, integration: IntegrationAccount) -> str:
        """Refresh expired access token."""
        refresh_token = integration.metadata_.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "NO_REFRESH_TOKEN",
                        "message": "No refresh token available",
                    }
                },
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                QUICKBOOKS_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET),
                headers={"Accept": "application/json"},
            )

        if response.status_code != 200:
            integration.status = "expired"
            await self.db.commit()
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "REFRESH_FAILED",
                        "message": "Failed to refresh token",
                    }
                },
            )

        token_data = response.json()
        integration.access_token_encrypted = token_data.get("access_token")
        integration.metadata_["refresh_token"] = token_data.get("refresh_token", refresh_token)
        integration.metadata_["expires_in"] = token_data.get("expires_in", 3600)
        await self.db.commit()

        return integration.access_token_encrypted

    async def get_connection_status(self, business_id: UUID) -> dict:
        """Check QuickBooks connection status for a business."""
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "quickbooks",
            )
        )
        integration = result.scalar_one_or_none()
        if not integration or integration.status != "active":
            return {"connected": False}
        return {
            "connected": True,
            "company_id": integration.external_id,
            "company_name": integration.metadata_.get("company_name"),
            "last_synced_at": integration.last_synced_at,
        }

    async def disconnect(self, business_id: UUID) -> None:
        """Disconnect QuickBooks integration."""
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "quickbooks",
            )
        )
        integration = result.scalar_one_or_none()
        if integration:
            # Revoke token if we have credentials
            if settings.QUICKBOOKS_CLIENT_ID and integration.access_token_encrypted:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            QUICKBOOKS_REVOKE_URL,
                            data={"token": integration.access_token_encrypted},
                            auth=(settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET),
                        )
                except Exception:
                    pass  # Best effort revocation

            await self.db.delete(integration)
            await self.db.commit()

    async def sync_financial_data(self, business_id: UUID) -> dict:
        """Pull financial data from QuickBooks and return metrics."""
        result = await self.db.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.business_id == business_id,
                IntegrationAccount.provider == "quickbooks",
            )
        )
        integration = result.scalar_one_or_none()
        if not integration or integration.status != "active":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "NOT_CONNECTED",
                        "message": "QuickBooks not connected",
                    }
                },
            )

        access_token = integration.access_token_encrypted
        realm_id = integration.external_id
        api_base = self._get_api_base()

        # Fetch P&L report
        revenue_data = await self._fetch_profit_and_loss(access_token, realm_id, api_base)

        # Fetch invoices for transaction count
        invoice_count = await self._fetch_invoice_count(access_token, realm_id, api_base)

        # Fetch credit memos for refund data
        refund_data = await self._fetch_refund_data(access_token, realm_id, api_base)

        # Update last_synced_at
        from datetime import datetime, timezone
        integration.last_synced_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "revenue_total": revenue_data.get("total_income"),
            "transaction_count": invoice_count,
            "refund_count": refund_data.get("count", 0),
            "refund_ratio": refund_data.get("ratio"),
            "chargeback_count": None,  # Not available in QuickBooks
            "chargeback_ratio": None,
            "payout_reliability": None,  # Not applicable
        }

    async def _fetch_profit_and_loss(
        self, access_token: str, realm_id: str, api_base: str
    ) -> dict:
        """Fetch P&L report from QuickBooks."""
        url = f"{api_base}/v3/company/{realm_id}/reports/ProfitAndLoss"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                params={"date_macro": "This Fiscal Year-to-date"},
            )

        if response.status_code != 200:
            return {"total_income": None}

        data = response.json()
        # Parse P&L structure to get total income
        rows = data.get("Rows", {}).get("Row", [])
        for row in rows:
            if row.get("group") == "Income":
                summary = row.get("Summary", {})
                col_data = summary.get("ColData", [])
                if len(col_data) > 1:
                    return {"total_income": float(col_data[1].get("value", 0))}
        return {"total_income": None}

    async def _fetch_invoice_count(
        self, access_token: str, realm_id: str, api_base: str
    ) -> int:
        """Fetch invoice count from QuickBooks."""
        url = f"{api_base}/v3/company/{realm_id}/query"
        query = "SELECT COUNT(*) FROM Invoice"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                params={"query": query},
            )

        if response.status_code != 200:
            return 0

        data = response.json()
        return data.get("QueryResponse", {}).get("totalCount", 0)

    async def _fetch_refund_data(
        self, access_token: str, realm_id: str, api_base: str
    ) -> dict:
        """Fetch refund/credit memo data from QuickBooks."""
        url = f"{api_base}/v3/company/{realm_id}/query"
        query = "SELECT COUNT(*) FROM CreditMemo"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                params={"query": query},
            )

        if response.status_code != 200:
            return {"count": 0, "ratio": None}

        data = response.json()
        count = data.get("QueryResponse", {}).get("totalCount", 0)

        # Calculate ratio if we have invoice count
        invoice_count = await self._fetch_invoice_count(access_token, realm_id, api_base)
        ratio = count / invoice_count if invoice_count > 0 else None

        return {"count": count, "ratio": ratio}
