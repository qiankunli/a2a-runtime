from abc import ABC, abstractmethod
from typing import AsyncGenerator

from server.common.model import AgentConfig


class Notifier(ABC):
    @abstractmethod
    async def watch(self) -> AsyncGenerator[AgentConfig, None]:
        pass

