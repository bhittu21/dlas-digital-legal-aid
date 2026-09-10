import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.v1.router import api_router
from app.realtime.connection_manager import manager
from app.services.seed_service import seed_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dlas.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    Initializes database schema and executes idempotent seed data on startup.
    """
    logger.info("Initializing DLAS authoritative database schema...")
    Base.metadata.create_all(bind=engine)

    # Seed demo data for Bangladesh legal aid
    db = SessionLocal()
    try:
        logger.info("Checking and seeding realistic Bangladesh legal aid cases...")
        seed_database(db)
        logger.info("Database initialization and seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error during database startup seed: {e}")
        db.rollback()
    finally:
        db.close()

    yield

    logger.info("Shutting down DLAS backend services...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Authoritative backend service for the Bangladesh Digital Legal Aid System (DLAS).",
    lifespan=lifespan,
)

# Configure CORS for Vercel frontend & local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 REST API
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


from pathlib import Path
from fastapi.staticfiles import StaticFiles

@app.get("/api/info")
def api_info():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_PREFIX}/health",
        "ws_url": "/ws",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Realtime WebSocket hub for DLAO Officers and Panel Lawyers.
    Broadcasts case state changes, priority adjustments, lawyer assignments, and notifications.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive client messages (e.g. heartbeat ping/pong)
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)


# Mount production frontend static files if present (must be after all API and WS routes)
src_dir = Path(__file__).resolve().parent.parent.parent / "src"
if src_dir.exists():
    app.mount("/", StaticFiles(directory=str(src_dir), html=True), name="frontend")

