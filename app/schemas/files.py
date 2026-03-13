from pydantic import BaseModel, Field

class PresignedPostResponse(BaseModel):
    url:str
    fields:dict[str, str]


