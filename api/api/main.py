"""App factory: mounts routers, configures CORS for the local frontend."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import errors, live, missions, status

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(title="Roomba Telemetry API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(status.router)
    app.include_router(missions.router)
    app.include_router(errors.router)
    app.include_router(live.router)

    return app


app = create_app()
