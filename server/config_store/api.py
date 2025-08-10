import logging

from typing import Dict, List

import httpx

from server.common.model import AgentConfig, namespace_name
from server.config_store.base import AgentConfigStore
from server.utils.map import extract_nested_data

logger = logging.getLogger(__name__)


class APIAgentConfigStore(AgentConfigStore):
    # todo 后续支持api方式获取agent config
    def __init__(self, url: str, config_json_path: str = 'data', timeout: int = 10):
        self.url = url
        self.config_json_path = config_json_path
        self.timeout = timeout
        self._agent_config_cache: Dict[str, AgentConfig] = {}

    async def list(self) -> List[AgentConfig]:
        # 从http url 中获取agent config list
        agent_configs = await self.read_url()
        self._agent_config_cache = {agent_config.namespace_name: agent_config for agent_config in agent_configs}
        return agent_configs

    async def read_url(self) -> List[AgentConfig]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.url)
                response.raise_for_status()
                raw_data = response.json()
                agent_config_data = extract_nested_data(raw_data, self.config_json_path)
                if not agent_config_data or not isinstance(agent_config_data, list):
                    raise ValueError(f'No valid agent config data found in path {self.config_json_path}')
                return [AgentConfig.parse_obj(config) for config in agent_config_data if config]
            except httpx.HTTPError as e:
                # 处理HTTP相关错误（连接超时、网络错误、状态码错误等）
                logger.error(f'HTTP request failed: {str(e)}')
            except ValueError as e:
                # 处理JSON解析错误
                logger.error(f'Failed to parse config response: {str(e)}')
        return []

    async def get(self, namespace: str, name: str) -> AgentConfig:
        _name = namespace_name(namespace, name)
        if _name in self._agent_config_cache:
            return self._agent_config_cache[_name]
        raise ValueError(f'No agent config found for agent {namespace_name}')

    async def upsert(self, agent_config: AgentConfig):
        self._agent_config_cache[agent_config.namespace_name] = agent_config

    async def delete(self, agent_config: AgentConfig):
        del self._agent_config_cache[agent_config.namespace_name]
