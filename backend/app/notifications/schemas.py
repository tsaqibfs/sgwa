from pydantic import BaseModel


class UnreadCount(BaseModel):
    count: int
