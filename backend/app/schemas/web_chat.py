from pydantic import BaseModel, Field, field_validator


class WebChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: str = Field(..., max_length=20)

    @field_validator("session_id")
    @classmethod
    def session_id_must_start_with_web(cls, v: str) -> str:
        if not v.startswith("web_"):
            raise ValueError("session_id must start with 'web_'")
        return v


class WebChatResponse(BaseModel):
    reply: str
    reply_type: str
    quick_replies: list[str]
