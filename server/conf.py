#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from server.common.model import RedisClusterType

# 获取项目根目录
BasePath = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"{BasePath}/.env", env_file_encoding="utf-8", extra="ignore"
    )

    # Env MySQL
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_ENGINE: str = "mysql+aiomysql"
    DB_HOST: str = ""
    DB_PORT: int = 3306
    DB_DATABASE: str = "test"
    DB_ECHO: bool = False
    DB_CHARSET: str = "utf8mb4"

    SQLALCHEMY_DATABASE_URL: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URL", mode="before")
    def assemble_mysql_connection(  # pylint: disable=no-self-argument
            cls, v: str, info: ValidationInfo
    ):
        if len(v) == 0:
            # 部分客户用户名和密码可能带@字符
            username = quote_plus(info.data["DB_USERNAME"])
            password = quote_plus(info.data["DB_PASSWORD"])
            return (
                f"{info.data['DB_ENGINE']}://{username}:{password}@"
                f"{info.data['DB_HOST']}:{info.data['DB_PORT']}/{info.data['DB_DATABASE']}?charset={info.data['DB_CHARSET']}"
            )
        return v

    # redis config
    REDIS_USE_SSL: bool = False
    REDIS_ADDRESS: str = "localhost:6379"
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_CLUSTER_TYPE: RedisClusterType = RedisClusterType.SINGLE
    REDIS_TIMEOUT: int = 5
    # Env Sentinel
    REDIS_MASTER_NAME: str = "mymaster"

    # unicorn
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 9999

    NOTIFIER_TYPE: str | None = None
    NOTIFIED_REDIS_CHANNEL: str | None = None

    CONFIG_RELOAD_INTERVAL_SECONDS: int = 10 * 60


settings = Settings()
