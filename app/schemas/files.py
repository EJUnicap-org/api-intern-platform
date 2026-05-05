from pydantic import BaseModel

class UploadUrlRequest(BaseModel):
    file_name: str
    content_type: str

class UploadUrlResponse(BaseModel):
    upload_url: str
    method: str = "PUT"
    file_url: str  