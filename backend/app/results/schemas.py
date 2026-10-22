from pydantic import BaseModel

DEMO_LABEL = 'Bukti hasil demonstrasi akademik — bukan dokumen resmi'


class ResultOut(BaseModel):
    id: int
    number: str
    request_id: int
    snapshot: dict
    label: str = DEMO_LABEL
