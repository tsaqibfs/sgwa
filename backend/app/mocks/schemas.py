from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class MockRun(BaseModel):
    model_config = ConfigDict(extra='forbid')
    check_type: Literal['identity', 'permit_completeness', 'general_service']
    scenario: Literal['success', 'mismatch', 'unavailable']
    idempotency_key: str = Field(min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
