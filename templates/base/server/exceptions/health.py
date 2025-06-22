from fastapi import status
from server.exceptions.base import ServerException


class HealthCheckFailedException(ServerException):
    """Raised when the health check fails."""


class DatabaseHealthCheckFailedException(ServerException):
    """Raised when the database health check fails."""


class CacheHealthCheckFailedException(ServerException):
    """Raised when the cache health check fails."""


HEALTH_EXCEPTIONS = {
    HealthCheckFailedException: {
        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
        "detail": {
            "message": "The service is currently unavailable",
            "error_code": "health_check_failed",
        },
    },
    DatabaseHealthCheckFailedException: {
        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
        "detail": {
            "message": "The database is currently unavailable",
            "error_code": "database_health_check_failed",
        },
    },
    CacheHealthCheckFailedException: {
        "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
        "detail": {
            "message": "The cache is currently unavailable",
            "error_code": "cache_health_check_failed",
        },
    },
}
