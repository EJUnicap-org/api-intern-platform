from pydantic import BaseModel
from typing import Optional

class UploadUrlRequest(BaseModel):
    file_name: str
    content_type: str
    folder: Optional[str] = "misc"

class UploadUrlResponse(BaseModel):
    upload_url: str
    method: str = "PUT"
    file_url: str  