import json
import logging

from typing import AsyncGenerator

from redis.asyncio import RedisCluster

from server.common.model import AgentConfig
from server.libs.redis.client import RedisConfig, get_redis_client
from server.notifier.base import Notifier

logger = logging.getLogger(__name__)


class RedisNotifier(Notifier):
    def __init__(self, config: RedisConfig, channel: str = 'agent_config_updates'):
        self.channel = channel
        self.client = get_redis_client(config)

    async def watch(self) -> AsyncGenerator[AgentConfig, None]:
        if isinstance(self.client, RedisCluster):
            raise ValueError('Redis cluster mode is not supported for Pub/Sub.')
        async with self.client.pubsub() as pubsub:
            await pubsub.subscribe(self.channel)
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        config_data = json.loads(message['data'])
                        yield AgentConfig(**config_data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON format in message: {message['data']}")
                    except Exception as e:
                        logger.error(f'Failed to parse AgentConfig: {str(e)}')
