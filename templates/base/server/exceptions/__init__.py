from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from server.exceptions.base import ServerException
from server.exceptions.auth import AUTH_EXCEPTIONS
from server.exceptions.user import USER_EXCEPTIONS
from server.exceptions.health import HEALTH_EXCEPTIONS

__all__ = ['ServerException', 'AUTH_EXCEPTIONS', 'USER_EXCEPTIONS']

def register_exceptions(app: FastAPI):
    _register_auth_exceptions(app)
    _register_user_exceptions(app)
    _register_health_exceptions(app)

def _register_auth_exceptions(app: FastAPI):
    for exc, config in AUTH_EXCEPTIONS.items():
        app.add_exception_handler(
            exc,
            _create_exception_handler(
                config["status_code"], 
                config["detail"],
                headers=config.get("headers")
            )
        )

def _register_user_exceptions(app: FastAPI):
    for exc, config in USER_EXCEPTIONS.items():
        app.add_exception_handler(
            exc,
            _create_exception_handler(
                config["status_code"], 
                config["detail"],
                headers=config.get("headers")
            )
        )

def _register_health_exceptions(app: FastAPI):
    for exc, config in HEALTH_EXCEPTIONS.items():
        app.add_exception_handler(
            exc,
            _create_exception_handler(
                config["status_code"], 
                config["detail"],
                headers=config.get("headers")
            )
        )

def _create_exception_handler(status_code: int, detail: Any, headers: Optional[Dict[str, str]] = None):
    async def _exception_handler(request: Request, exc: Exception):
        response =  JSONResponse(
            content=detail,
            status_code=status_code,
        )
        if headers:
            response.headers.update(headers)
        
        return response

    return _exception_handler

