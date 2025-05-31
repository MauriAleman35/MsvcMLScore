from beanie import Document
from typing import Optional
from datetime import datetime,timezone
from pydantic import Field

class OfferDocument(Document):
    id: int
    id_solicitude: int
    partner_id: int
    interest: float
    loan_term:int
    monthly_payment: float
    total_repayment_amount: float
    status: str="aceptada"
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))


    class Settings:
        name = "offer"  # Nombre de la colección en MongoDB
        use_state_management = True