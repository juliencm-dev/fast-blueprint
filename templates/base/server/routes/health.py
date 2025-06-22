from datetime import datetime
from enum import Enum
from typing import Dict

import psutil
from fastapi import APIRouter
from pydantic import BaseModel
from server.config import settings as s
from server.db import check_cache
from server.db import check_database
from server.utils import nowutc
from server.utils.core.logging.logger import logger


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DatabaseStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class CacheStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class HealthCheckResponse(BaseModel):
    name: str
    version: str
    environment: str
    status: ServiceStatus
    timestamp: datetime
    system: Dict[str, float]
    database: DatabaseStatus
    cache: CacheStatus


router = APIRouter()


@router.get("/", response_model=HealthCheckResponse)
async def health_check() -> Dict:
    """Health check endpoint. Returns the status of the service."""

    status = ServiceStatus.HEALTHY
    db_status = DatabaseStatus.ONLINE
    cache_status = CacheStatus.ONLINE

    # NOTE: This is where you can add your own health check logic.👇
    try:
        await check_database()
    except Exception as e:
        logger.error(e)
        db_status = DatabaseStatus.OFFLINE
        status = ServiceStatus.DEGRADED

    try:
        await check_cache()
    except Exception as e:
        logger.error(e)
        cache_status = CacheStatus.OFFLINE
        status = ServiceStatus.DEGRADED

    return {
        "name": s.APP_NAME,
        "version": s.VERSION,
        "environment": s.FASTAPI_ENV,
        "status": status,
        "timestamp": nowutc(),
        "system": {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
        },
        "database": db_status,
        "cache": cache_status,
    }
