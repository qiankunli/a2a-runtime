from typing import List

from server.common.model import AgentConfig, namespace_name
from server.config_store.base import AgentConfigStore


class DefaultAgentConfigStore(AgentConfigStore):
    # todo 后续支持api方式获取agent config
    def __init__(self, agent_configs: List[AgentConfig]):
        self.agent_configs = agent_configs
        self._agent_config_cache = {agent_config.namespace_name: agent_config for agent_config in agent_configs}

    async def list(self) -> List[AgentConfig]:
        return self.agent_configs

    async def reload(self) -> None:
        pass

    async def get(self, namespace: str, name: str) -> AgentConfig:
        _name = namespace_name(namespace, name)
        if _name in self._agent_config_cache:
            return self._agent_config_cache[_name]
        raise ValueError(f'No agent config found for agent {namespace_name}')

    async def upsert(self, agent_config: AgentConfig):
        self._agent_config_cache[agent_config.namespace_name] = agent_config

    async def delete(self, agent_config: AgentConfig):
        del self._agent_config_cache[agent_config.namespace_name]
