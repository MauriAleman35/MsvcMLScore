from beanie import Document
from pydantic import Field  # Importar Field desde pydantic, no desde beanie
from datetime import datetime
from typing import Optional, List
class UserDocument(Document):
    id: int = Field(..., description="ID del usuario (mismo que en ERP)")
    name: str
    last_name: str
    user_type: str = "prestatario"
    email: Optional[str] = None
    adress_verified: bool = False
    identity_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    
    # Configuración del documento
    class Settings:
        name = "user"  # Nombre de la colección en MongoDB
        use_state_management = True