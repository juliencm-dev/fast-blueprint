from redis import asyncio as aioredis
from server.config import settings as s
from server.exceptions.health import CacheHealthCheckFailedException
from server.exceptions.health import DatabaseHealthCheckFailedException
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel import literal_column
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

ENV = s.FASTAPI_ENV == "development"
DB_URL = s.DEV_DATABASE_URL if ENV else s.PROD_DATABASE_URL


# NOTE: PostgreSQL Database layer is managed with sqlmodel/sqlalchemy:

db_engine = create_async_engine(
    url=DB_URL,
    echo=ENV,
)


async def create_db():
    async with db_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def get_session():
    Session = AsyncSession(db_engine, expire_on_commit=False)
    async with Session as session:
        yield session


async def check_database():
    async with AsyncSession(db_engine) as session:
        result = await session.exec(select(literal_column("1")))

        if not result.first():
            raise DatabaseHealthCheckFailedException()


# NOTE: Cache layer is managed with Redis:

cache: aioredis.Redis | None = None


async def get_cache():
    if not cache:
        raise CacheHealthCheckFailedException()
    return cache


async def init_cache():
    global cache
    cache = aioredis.Redis(
        host=s.REDIS_HOST,
        port=s.REDIS_PORT,
        db=0,
        password=s.REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_cache():
    global cache

    if cache:
        await cache.close()


async def check_cache():
    global cache

    if not cache:
        raise CacheHealthCheckFailedException("Redis client is not initialized.")

    try:
        result = await cache.ping()
        if not result:
            raise CacheHealthCheckFailedException("Redis did not respond with PONG.")
    except aioredis.RedisError as e:
        raise CacheHealthCheckFailedException(f"Redis error: {e}")
