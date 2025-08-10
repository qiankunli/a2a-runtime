from enum import Enum
from typing import Any, Dict

from a2a.types import AgentCard
from pydantic import BaseModel

X_AGENT_NAMESPACE = 'x-agent-namespace'
X_AGENT_NAME = 'x-agent-name'


class RedisClusterType(str, Enum):
    SINGLE = "single"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"


class SyncOperation(str, Enum):
    UPSERT = 'upsert'
    DELETE = 'delete'


class AgentConfig(BaseModel):
    namespace: str
    name: str
    card: Dict[str, Any]
    extended_card: Dict[str, Any] | None = None

    sync_operation: SyncOperation | None = None

    @property
    def namespace_name(self) -> str:
        return namespace_name(self.namespace, self.name)

    def get_card(self) -> AgentCard:
        return AgentCard(**self.card)

    def get_extended_card(self) -> AgentCard:
        return AgentCard(**self.extended_card)


def namespace_name(namespace: str, name: str) -> str:
    return f'{namespace}/{name}'
