from __future__ import annotations
from beanie import Document, Indexed
from datetime import datetime,timezone
from typing import Optional
from pydantic import Field, validator
from bson import ObjectId


class Loan(Document):
    # Mongo crea _id (ObjectId) automáticamente ― no lo declares si no lo necesitas
    id:        int                  # índice único opcional
    id_offer:  int

    loan_amount:       float
    start_date:        datetime
    end_date:          Optional[datetime]   = None

    hash_blockchain:   str
    current_status:    str                  # "al_dia" | "en_mora" | "mora_grave"
    late_payment_count:int                  = 0

    last_status_update:datetime             = Field(default_factory=datetime.now(timezone.utc))
    created_at:         datetime            = Field(default_factory=datetime.now(timezone.utc))
    updated_at:         datetime            = Field(default_factory=datetime.now(timezone.utc))

    # --- validación / conversión extra ---------------------------------
    @validator("start_date", "end_date", "last_status_update", pre=True)
    def parse_dates(cls, v):
        # Acepta ISO-strings como "2025-05-19 22:39:00"
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace(" ", "T"))
        return v

    class Settings:
        name = "loan"          # nombre exacto de la colección
