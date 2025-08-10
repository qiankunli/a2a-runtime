from abc import ABC, abstractmethod
from typing import List

from server.common.model import AgentConfig, SyncOperation


class AgentConfigStore(ABC):
    @abstractmethod
    async def list(self) -> List[AgentConfig]:
        pass

    @abstractmethod
    async def reload(self) -> None:
        pass

    @abstractmethod
    async def get(self, namespace: str, name: str) -> AgentConfig:
        pass

    async def sync_agent_config(self, agent_config: AgentConfig) -> None:
        if not agent_config.sync_operation:
            return
        if agent_config.sync_operation == SyncOperation.UPSERT:
            await self.upsert(agent_config)
        elif agent_config.sync_operation == SyncOperation.DELETE:
            await self.delete(agent_config)

    @abstractmethod
    async def upsert(self, agent_config: AgentConfig) -> None:
        pass

    @abstractmethod
    async def delete(self, agent_config: AgentConfig) -> None:
        pass
