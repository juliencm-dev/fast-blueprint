from datetime import datetime
from enum import Enum

import sqlalchemy.dialects.postgresql as pg
from server.utils import cuid
from server.utils import nowutc
from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import Index
from sqlmodel import SQLModel


class ValidationTokenType(str, Enum):
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"


class ValidationToken(SQLModel, table=True):
    __tablename__ = "validation_tokens"
    user_id: str = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    token: str = Field(
        sa_column=Column(
            pg.VARCHAR(length=255), nullable=False, unique=True, primary_key=True
        )
    )
    token_type: ValidationTokenType = Field(
        sa_column=Column(pg.ENUM(ValidationTokenType), nullable=False)
    )
    expires_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), default=nowutc)
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    jti: str = Field(
        sa_column=Column(pg.VARCHAR(length=24), unique=True, primary_key=True)
    )
    user_id: str = Field(foreign_key="users.id", ondelete="CASCADE")
    device_id: str = Field(foreign_key="devices.id", ondelete="CASCADE")
    expires_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), default=nowutc)
    )


class Device(SQLModel, table=True):
    __tablename__ = "devices"
    __table_args__ = (
        Index(
            "compound_index_user_agent_user_id_ip_address",
            "raw_user_agent",
            "ip_address",
            "user_id",
            unique=True,
        ),
    )
    id: str = Field(
        default_factory=cuid,
        sa_column=Column(
            pg.VARCHAR(length=24),
            primary_key=True,
        ),
    )
    user_id: str = Field(foreign_key="users.id", ondelete="CASCADE")
    browser: str = Field(
        sa_column=Column(
            pg.VARCHAR(length=50),
        )
    )
    browser_version: str = Field(
        sa_column=Column(
            pg.VARCHAR(length=50),
        )
    )
    os: str = Field(
        sa_column=Column(
            pg.VARCHAR(length=50),
        )
    )
    device_type: str = Field(
        sa_column=Column(
            pg.VARCHAR(length=50),
        )
    )
    is_mobile: bool
    is_tablet: bool
    is_desktop: bool
    raw_user_agent: str
    ip_address: str = Field(
        sa_column=Column(
            pg.VARCHAR(length=50),
        )
    )
    last_seen: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), default=nowutc)
    )
