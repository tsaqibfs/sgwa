from datetime import datetime
from pydantic import BaseModel


class AuditOut(BaseModel):
    id:int
    actor_id:int|None
    actor_name:str|None
    action:str
    entity_type:str
    entity_id:int
    changes:dict
    created_at:datetime
