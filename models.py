from pydantic import BaseModel


class TrackRequest(BaseModel):
    tracking_id: str
    max_retries: int = 10
