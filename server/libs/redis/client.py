# 根据URL返回redis client（支持单机/哨兵/集群模式）
import logging

from typing import Any, Dict, List, Tuple

import redis.asyncio as redis

from pydantic import BaseModel
from redis.asyncio.cluster import ClusterNode, RedisCluster
from redis.asyncio.sentinel import Sentinel

from server.common.model import RedisClusterType
from server.conf import settings

# 全局连接池配置
DEFAULT_POOL_CONFIG: Dict[str, Any] = {
    'max_connections': 20,
    'retry_on_timeout': True,
    'encoding': 'utf-8',
    'socket_timeout': 5.0,
    'socket_connect_timeout': 3.0,
}

# 初始化日志
logger = logging.getLogger(__name__)


class RedisConfig(BaseModel):
    cluster_type: RedisClusterType
    address: str
    db: int
    username: str
    password: str
    master_name: str
    timeout: int
    use_ssl: bool

    @classmethod
    def from_settings(cls) -> "RedisConfig":
        return cls(
            cluster_type=settings.REDIS_CLUSTER_TYPE,
            address=settings.REDIS_ADDRESS,
            db=settings.REDIS_DB,
            username=settings.REDIS_USERNAME,
            password=settings.REDIS_PASSWORD,
            master_name=settings.REDIS_MASTER_NAME,
            timeout=settings.REDIS_TIMEOUT,
            use_ssl=settings.REDIS_USE_SSL,
        )


def get_redis_client(config: RedisConfig) -> redis.Redis | redis.StrictRedis | RedisCluster:
    if config.cluster_type == RedisClusterType.SINGLE:
        host, port = config.address.split(":")
        return redis.Redis(
            host=host,
            port=int(port),
            username=config.username or None,
            password=config.password or None,
            db=config.db,
            socket_timeout=config.timeout,
            ssl=config.use_ssl
        )

    elif config.cluster_type == RedisClusterType.SENTINEL:
        sentinel_hosts: List[Tuple[str, int]] = [
            (h, int(p)) for h, p in (addr.split(":") for addr in config.address.split(","))
        ]
        sentinel = Sentinel(
            sentinel_hosts,
            socket_timeout=config.timeout,
            password=config.password or None,
            ssl=config.use_ssl
        )
        return sentinel.master_for(
            service_name=config.master_name,
            username=config.username or None,
            password=config.password or None,
            db=config.db,
            socket_timeout=config.timeout,
            ssl=config.use_ssl
        )

    elif config.cluster_type == RedisClusterType.CLUSTER:
        startup_nodes = [
            ClusterNode(host=h, port=int(p))  
            for h, p in (addr.split(":") for addr in config.address.split(","))
        ]
        return RedisCluster(
            startup_nodes=startup_nodes,
            username=config.username or None,
            password=config.password or None,
            socket_timeout=config.timeout,
            ssl=config.use_ssl,
            decode_responses=True
        )

    else:
        raise ValueError(f"Unsupported RedisClusterType: {config.cluster_type}")
