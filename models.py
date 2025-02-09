from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    query_text: str

class QueryResponse(BaseModel):
    query: str
    response: str
    image_ids: List[str]

class ImageUploadResponse(BaseModel):
    status: str
    image_id: str
