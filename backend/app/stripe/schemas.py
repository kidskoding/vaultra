from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConnectionStatus(BaseModel):
    connected: bool
    account_id: Optional[str] = None
    last_synced_at: Optional[datetime] = None
