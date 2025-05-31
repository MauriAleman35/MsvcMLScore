from beanie import Document,Field 
from datetime import datetime
from typing import Optional
class UserDocument(Document):
    id: int = Field(..., description="ID del usuario (mismo que en ERP)")
    name: str
    last_name: str
    user_type: str = "prestatario"
    email: Optional[str] = None
    adress_verified: bool = False
    identity_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    
    # Configuración del documento
    class Settings:
        name = "user"  # Nombre de la colección en MongoDB
        use_state_management = True