"""FastAPI application for the dashboard API."""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    CharacterInfo,
    CommentData,
    ConfigUpdate,
    ConversationEntry,
    ManualMessageRequest,
    PipelineStatus,
    ResponseData,
    SystemStats,
    WebSocketMessage,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="AITuber Dashboard API",
        description="Web dashboard API for AITuber Starter Kit",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store for pipeline reference and state
    app.state.pipeline = None
    app.state.pipeline_status = PipelineStatus.STOPPED
    app.state.start_time: Optional[datetime] = None
    app.state.stats = {
        "comments_processed": 0,
        "responses_generated": 0,
    }
    app.state.recent_comments: list[CommentData] = []
    app.state.recent_responses: list[ResponseData] = []
    app.state.websocket_clients: list[WebSocket] = []
    app.state.memory_store = None  # Long-term memory store

    # Register routes
    _register_routes(app)

    # Mount static files (dashboard UI)
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all API routes.

    Args:
        app: FastAPI application instance.
    """

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/api/status", response_model=SystemStats)
    async def get_status():
        """Get current system status."""
        import psutil

        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        uptime = 0.0
        if app.state.start_time:
            uptime = (datetime.now() - app.state.start_time).total_seconds()

        queue_size = 0
        if app.state.pipeline and hasattr(app.state.pipeline, "comment_queue"):
            queue_size = len(app.state.pipeline.comment_queue)

        return SystemStats(
            status=app.state.pipeline_status,
            uptime_seconds=uptime,
            comments_processed=app.state.stats["comments_processed"],
            responses_generated=app.state.stats["responses_generated"],
            queue_size=queue_size,
            memory_usage_mb=memory_mb,
        )

    @app.post("/api/pipeline/start")
    async def start_pipeline():
        """Start the AITuber pipeline."""
        if app.state.pipeline_status == PipelineStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Pipeline already running")

        if not app.state.pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not configured")

        try:
            app.state.pipeline_status = PipelineStatus.STARTING
            await _broadcast_status(app)

            # Start pipeline in background task
            asyncio.create_task(app.state.pipeline.start())

            app.state.pipeline_status = PipelineStatus.RUNNING
            app.state.start_time = datetime.now()
            await _broadcast_status(app)

            return {"message": "Pipeline started", "status": "running"}
        except Exception as e:
            app.state.pipeline_status = PipelineStatus.ERROR
            await _broadcast_status(app)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/pipeline/stop")
    async def stop_pipeline():
        """Stop the AITuber pipeline."""
        if app.state.pipeline_status != PipelineStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Pipeline not running")

        if not app.state.pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not configured")

        try:
            app.state.pipeline_status = PipelineStatus.STOPPING
            await _broadcast_status(app)

            await app.state.pipeline.stop()

            app.state.pipeline_status = PipelineStatus.STOPPED
            await _broadcast_status(app)

            return {"message": "Pipeline stopped", "status": "stopped"}
        except Exception as e:
            app.state.pipeline_status = PipelineStatus.ERROR
            await _broadcast_status(app)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/comments", response_model=list[CommentData])
    async def get_recent_comments(limit: int = 50):
        """Get recent comments."""
        return app.state.recent_comments[-limit:]

    @app.get("/api/responses", response_model=list[ResponseData])
    async def get_recent_responses(limit: int = 50):
        """Get recent AI responses."""
        return app.state.recent_responses[-limit:]

    @app.get("/api/conversations", response_model=list[ConversationEntry])
    async def get_conversations(limit: int = 50):
        """Get recent conversation entries."""
        conversations = []
        for response in app.state.recent_responses[-limit:]:
            conversations.append(
                ConversationEntry(
                    id=response.id,
                    user_name=response.user_name,
                    user_message=response.user_message,
                    ai_response=response.ai_response,
                    emotion=response.emotion,
                    timestamp=response.timestamp,
                )
            )
        return conversations

    @app.post("/api/message")
    async def send_manual_message(request: ManualMessageRequest):
        """Send a manual message to the AI."""
        if not app.state.pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not configured")

        if app.state.pipeline_status != PipelineStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Pipeline not running")

        try:
            response = await app.state.pipeline.respond_to_text(
                request.message,
                user_name=request.user_name,
            )

            response_data = ResponseData(
                id=str(uuid.uuid4()),
                user_name=request.user_name,
                user_message=request.message,
                ai_response=response,
                timestamp=datetime.now(),
            )
            app.state.recent_responses.append(response_data)
            app.state.stats["responses_generated"] += 1

            await _broadcast_response(app, response_data)

            return {"response": response, "id": response_data.id}
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/config")
    async def get_config():
        """Get current configuration."""
        if not app.state.pipeline:
            return {"error": "Pipeline not configured"}

        config = {
            "llm": {
                "provider": getattr(
                    app.state.pipeline.llm_client, "provider_name", "unknown"
                ),
                "model": getattr(app.state.pipeline.llm_client, "model", "unknown"),
                "temperature": getattr(
                    app.state.pipeline.llm_client, "temperature", 0.7
                ),
            },
            "tts": {
                "engine": getattr(
                    app.state.pipeline.tts_engine, "engine_name", "unknown"
                ),
                "speaker_id": app.state.pipeline.speaker_id,
                "speed": getattr(app.state.pipeline.tts_engine, "speed", 1.0),
            },
            "response_interval": app.state.pipeline.response_interval,
        }
        return config

    @app.patch("/api/config")
    async def update_config(update: ConfigUpdate):
        """Update configuration (some settings require restart)."""
        if not app.state.pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not configured")

        changes = []

        # Update response interval (can be changed live)
        if update.response_interval is not None:
            app.state.pipeline.response_interval = update.response_interval
            changes.append(f"response_interval={update.response_interval}")

        # Update TTS speaker (can be changed live)
        if update.tts_speaker_id is not None:
            app.state.pipeline.speaker_id = update.tts_speaker_id
            changes.append(f"tts_speaker_id={update.tts_speaker_id}")

        # Update TTS speed (can be changed live)
        if update.tts_speed is not None:
            if hasattr(app.state.pipeline.tts_engine, "set_speed"):
                app.state.pipeline.tts_engine.set_speed(update.tts_speed)
                changes.append(f"tts_speed={update.tts_speed}")

        # Update LLM temperature (can be changed live)
        if update.llm_temperature is not None:
            if hasattr(app.state.pipeline.llm_client, "temperature"):
                app.state.pipeline.llm_client.temperature = update.llm_temperature
                changes.append(f"llm_temperature={update.llm_temperature}")

        # Note: Changing provider/model/engine requires restart
        restart_required = any(
            [
                update.llm_provider is not None,
                update.llm_model is not None,
                update.tts_engine is not None,
            ]
        )

        return {
            "changes": changes,
            "restart_required": restart_required,
            "message": "Configuration updated"
            + (" (restart required for some changes)" if restart_required else ""),
        }

    @app.get("/api/character", response_model=CharacterInfo)
    async def get_character():
        """Get current character information."""
        if not app.state.pipeline or not hasattr(
            app.state.pipeline.llm_client, "_character"
        ):
            raise HTTPException(status_code=400, detail="Character not configured")

        character = app.state.pipeline.llm_client._character
        if not character:
            raise HTTPException(status_code=404, detail="No character loaded")

        return CharacterInfo(
            name=character.name,
            personality=character.personality or "",
            first_person=character.speaking_style.get("first_person", "私")
            if character.speaking_style
            else "私",
            speaking_style=character.speaking_style.get("sentence_endings", [])
            if character.speaking_style
            else [],
            background=character.background,
        )

    @app.get("/api/memory/stats")
    async def get_memory_stats():
        """Get memory system statistics."""
        if not app.state.memory_store:
            return {
                "enabled": False,
                "total_entries": 0,
                "memory_type": "short-term only",
            }

        stats = await app.state.memory_store.get_stats()
        return {
            "enabled": True,
            "memory_type": "long-term",
            **stats,
        }

    @app.websocket("/api/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await websocket.accept()
        app.state.websocket_clients.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(app.state.websocket_clients)}")

        try:
            # Send initial status
            await websocket.send_json(
                WebSocketMessage(
                    type="status",
                    data={"status": app.state.pipeline_status.value},
                    timestamp=datetime.now(),
                ).model_dump(mode="json")
            )

            # Keep connection alive and handle messages
            while True:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=30.0,  # Ping every 30 seconds
                    )
                    # Handle incoming messages if needed
                    logger.debug(f"WebSocket received: {data}")
                except asyncio.TimeoutError:
                    # Send ping to keep alive
                    await websocket.send_json({"type": "ping"})

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            if websocket in app.state.websocket_clients:
                app.state.websocket_clients.remove(websocket)


async def _broadcast_status(app: FastAPI) -> None:
    """Broadcast status update to all WebSocket clients."""
    message = WebSocketMessage(
        type="status",
        data={"status": app.state.pipeline_status.value},
        timestamp=datetime.now(),
    )
    await _broadcast_message(app, message)


async def _broadcast_comment(app: FastAPI, comment: CommentData) -> None:
    """Broadcast new comment to all WebSocket clients."""
    message = WebSocketMessage(
        type="comment",
        data=comment.model_dump(mode="json"),
        timestamp=datetime.now(),
    )
    await _broadcast_message(app, message)


async def _broadcast_response(app: FastAPI, response: ResponseData) -> None:
    """Broadcast new response to all WebSocket clients."""
    message = WebSocketMessage(
        type="response",
        data=response.model_dump(mode="json"),
        timestamp=datetime.now(),
    )
    await _broadcast_message(app, message)


async def _broadcast_message(app: FastAPI, message: WebSocketMessage) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    disconnected = []
    for client in app.state.websocket_clients:
        try:
            await client.send_json(message.model_dump(mode="json"))
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket client: {e}")
            disconnected.append(client)

    # Remove disconnected clients
    for client in disconnected:
        if client in app.state.websocket_clients:
            app.state.websocket_clients.remove(client)
