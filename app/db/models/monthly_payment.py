from beanie import Document
from typing import Optional
from datetime import datetime,timezone
from pydantic import BaseModel, Field

class MonthlyPaymentDocument(Document):
    
    id:int
    id_loan:int
    due_date:datetime=Field(default_factory=datetime.now(timezone.utc))
    borrow_verified:bool
    partner_verified:bool
    days_late:int
    penalty_amount:float
    payment_status: str 
 
    class Sevttings:
        name = "monthly_payment"