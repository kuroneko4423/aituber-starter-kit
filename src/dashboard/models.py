"""Data models for the dashboard API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PipelineStatus(str, Enum):
    """Pipeline status enumeration."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class SystemStats(BaseModel):
    """System statistics model."""

    status: PipelineStatus = PipelineStatus.STOPPED
    uptime_seconds: float = 0.0
    comments_processed: int = 0
    responses_generated: int = 0
    queue_size: int = 0
    memory_usage_mb: float = 0.0


class CommentData(BaseModel):
    """Comment data for API responses."""

    id: str
    user_name: str
    message: str
    platform: str
    timestamp: datetime
    priority: int = 0
    is_donation: bool = False
    donation_amount: Optional[float] = None


class ResponseData(BaseModel):
    """Response data for API responses."""

    id: str
    comment_id: Optional[str] = None
    user_name: str
    user_message: str
    ai_response: str
    emotion: Optional[str] = None
    timestamp: datetime
    processing_time_ms: float = 0.0


class ConversationEntry(BaseModel):
    """A single conversation entry (user + AI response pair)."""

    id: str
    user_name: str
    user_message: str
    ai_response: str
    emotion: Optional[str] = None
    timestamp: datetime


class ConfigUpdate(BaseModel):
    """Configuration update request."""

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    tts_engine: Optional[str] = None
    tts_speaker_id: Optional[int] = None
    tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    response_interval: Optional[float] = Field(None, ge=1.0, le=60.0)


class ManualMessageRequest(BaseModel):
    """Request to send a manual message."""

    message: str = Field(..., min_length=1, max_length=500)
    user_name: str = Field(default="Dashboard User", max_length=100)


class CharacterInfo(BaseModel):
    """Character information."""

    name: str
    personality: str
    first_person: str
    speaking_style: list[str] = []
    background: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    type: str  # "status", "comment", "response", "error"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)
