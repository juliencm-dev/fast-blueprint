from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from server.config import settings as s
from server.db import create_db, init_cache, close_cache
from server.routes import auth, user, health
from server.middlewares import register_middlewares
from server.exceptions import register_exceptions
from server.services.auth.dependencies import get_current_active_user
from server.utils.core.logging.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # NOTE: This is where you can add your own startup logic.👇

    await create_db()
    await init_cache()

    try:
        yield
    finally:
        await close_cache()


def create_app():
    app = FastAPI(
        title="Your App Name",
        description="Project structure for your FastAPI app.",
        version=s.VERSION,
        docs_url=f"{s.API_PREFIX}/docs",
        openapi_url=f"{s.API_PREFIX}/openapi.json",
        contact={
            "name": "Developer",
            "email": "hello@juliencm.dev",
            "url": "https://juliencm.dev",
        },
        lifespan=lifespan,
    )

    if s.FASTAPI_ENV == "production":
        setup_logger()

    register_exceptions(app)
    register_middlewares(app)

    app.include_router(auth.router, prefix=f"{s.API_PREFIX}/auth", tags=["auth"])
    app.include_router(
        user.router,
        prefix=f"{s.API_PREFIX}/users",
        tags=["users"],
        dependencies=[Depends(get_current_active_user)],
    )
    app.include_router(health.router, prefix=f"{s.API_PREFIX}/health", tags=["health"])

    return app
