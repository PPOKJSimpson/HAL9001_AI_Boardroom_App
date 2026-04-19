from typing import Literal

from pydantic import BaseModel, Field, field_validator

SenderType = Literal["human", "agent", "system"]


class MessageCreate(BaseModel):
    sender: str
    senderType: SenderType
    text: str
    mentions: list[str] = Field(default_factory=list)
    replyTo: str | None = None

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class Message(MessageCreate):
    id: str
    roomId: str
    timestamp: str


class Participant(BaseModel):
    name: str
    type: SenderType
    role: str | None = None


class Session(BaseModel):
    id: str
    projectPath: str
    createdAt: str
    updatedAt: str
    roomName: str
    nextMessageId: int = 1
