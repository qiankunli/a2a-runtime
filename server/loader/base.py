from abc import ABC, abstractmethod

from a2a.server.agent_execution import AgentExecutor

from server.common.model import AgentConfig


class AgentLoader(ABC):
    @abstractmethod
    def load_executor(self, agent_config: AgentConfig) -> AgentExecutor:
        pass

