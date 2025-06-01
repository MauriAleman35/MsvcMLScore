import strawberry
from typing import Optional, Dict, List, Any, Union

# Tipo para representar las características de entrada
@strawberry.type
class InputFeatures:
    adress_verified: int = 0
    identity_verified: int = 0
    loan_count: int = 0
    late_payment_count: int = 0
    avg_days_late: float = 0.0
    total_penalty: float = 0.0
    payment_completion_ratio: float = 0.0
    has_no_late_payments: int = 0
    has_penalty: int = 0
    loans_al_dia_ratio: float = 0.0
    days_late_per_loan: float = 0.0

@strawberry.input
class ScorePredictionInput:
    adress_verified: int
    identity_verified: int
    loan_count: int
    late_payment_count: int
    avg_days_late: float
    total_penalty: float
    payment_completion_ratio: float
    has_no_late_payments: int
    has_penalty: int
    loans_al_dia_ratio: float
    days_late_per_loan: float

@strawberry.type
class ScorePredictionResult:
    score: float
    confidence: Optional[float] = None
    category: Optional[str] = None
    risk_level: Optional[str] = None
    explanation: Optional[list[str]] = None
    error: Optional[str] = None
    input_features: Optional["InputFeatures"] = None