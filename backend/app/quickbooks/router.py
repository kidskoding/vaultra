from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_db
from app.shared.deps import get_current_user
from app.shared.models import User
from app.config import settings
from app.quickbooks.service import QuickBooksService

router = APIRouter(tags=["quickbooks"])


@router.get("/integrations/quickbooks/connect")
async def quickbooks_connect(
    business_id: UUID,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate QuickBooks OAuth connection."""
    if not current_user and not settings.DEV_MODE:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"code": "UNAUTHORIZED", "message": "Authentication required"}
            },
        )
    service = QuickBooksService(db)
    url = await service.initiate_connect(business_id)
    return {"url": url}


@router.get("/integrations/quickbooks/callback")
async def quickbooks_callback(
    code: str | None = None,
    state: str | None = None,
    realmId: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from QuickBooks."""
    if error:
        return RedirectResponse(
            f"{settings.FRONTEND_BASE_URL}/onboarding/quickbooks-connect?error={error}"
        )

    if not code or not state or not realmId:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Missing required OAuth parameters",
                }
            },
        )

    service = QuickBooksService(db)
    await service.handle_oauth_callback(code, state, realmId)

    return RedirectResponse(
        f"{settings.FRONTEND_BASE_URL}/dashboard?business_id={state}"
    )


@router.get("/integrations/quickbooks/status")
async def quickbooks_status(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get QuickBooks connection status."""
    return await QuickBooksService(db).get_connection_status(business_id)


@router.delete("/integrations/quickbooks/disconnect")
async def quickbooks_disconnect(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect QuickBooks integration."""
    await QuickBooksService(db).disconnect(business_id)
    return {"status": "disconnected"}


@router.post("/integrations/quickbooks/sync")
async def quickbooks_sync(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger sync of QuickBooks financial data."""
    service = QuickBooksService(db)
    data = await service.sync_financial_data(business_id)
    return {"status": "synced", "data": data}
