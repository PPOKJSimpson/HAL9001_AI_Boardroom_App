from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import router as api_router

PROJECT_ROOT: Path = Path.cwd()


def create_app() -> FastAPI:
    from backend import storage

    storage.init_storage(PROJECT_ROOT)
    app = FastAPI(title="AI Boardroom", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app


app = create_app()
