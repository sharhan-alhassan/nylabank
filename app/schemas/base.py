from datetime import datetime
from pydantic import BaseModel


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


class BaseRetrieveResponseSchema(BaseModel):
    status: int
    detail: str

    class Config:
        from_attributes = True


class BaseResponseSchema(BaseModel):
    status: int
    detail: str

    class Config:
        from_attributes = True


class BaseTotalCountResponseSchema(BaseModel):
    status: int
    detail: str
    total_count: int

    class Config:
        from_attributes = True
