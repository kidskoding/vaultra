from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConnectionStatus(BaseModel):
    connected: bool
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    last_synced_at: Optional[datetime] = None
