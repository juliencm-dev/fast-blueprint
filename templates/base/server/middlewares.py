from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from server.config import settings as s


def register_middlewares(app):
    # NOTE: This is where you can add your own middlewares.

    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Set-Cookie"],
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=s.ALLOWED_HOSTS)
