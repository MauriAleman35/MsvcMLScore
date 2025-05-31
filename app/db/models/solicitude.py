from beanie import Document
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SolicitudeDocument(Document):
    id: int 
    borrower_id: int
    loan_amount: float
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "solicitude"  # Nombre de la colección en MongoDB