# API Models - Pydantic request/response models
from pydantic import BaseModel, Field
from typing import Any

class StimulusRequest(BaseModel):
    modality: str
    data: list[float]

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    brainState: dict = Field(default_factory=dict)

class ProactiveRequest(BaseModel):
    message: str

class MotorCommand(BaseModel):
    force: float = 0.0
    angle: float = 0.0
    velocity: float = 0.0
    joint: str = "arm"

class ReflexCheckRequest(BaseModel):
    force: float
    angle: float
    velocity: float

class GrepRequest(BaseModel):
    n: int
    url: str

class TrainRequest(BaseModel):
    n: int = 4
    include_user_inputs: bool = False
    briefing: str | None = None

class FeedbackRequest(BaseModel):
    valence: float
    message_id: int | None = None
    response_text: str | None = None

class YTRequest(BaseModel):
    url: str
    n: int = 1