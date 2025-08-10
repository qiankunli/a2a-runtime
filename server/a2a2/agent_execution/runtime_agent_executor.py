from typing import Tuple

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue

from server.common.model import X_AGENT_NAME, X_AGENT_NAMESPACE
from server.config_store.base import AgentConfigStore
from server.loader.base import AgentLoader


class RuntimeAgentExecutor(AgentExecutor):

    def __init__(self, agent_config_store: AgentConfigStore, agent_loader: AgentLoader):
        self.agent_config_store = agent_config_store
        self.agent_loader = agent_loader

    async def execute(
            self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        namespace, name = _get_agent(context)
        agent_config = await self.agent_config_store.get(namespace, name)
        if not agent_config:
            raise Exception('agent config not found')
        agent_executor = self.agent_loader.load_executor(agent_config)
        await agent_executor.execute(context, event_queue)

    async def cancel(
            self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        namespace, name = _get_agent(context)
        agent_config = await self.agent_config_store.get(namespace, name)
        if not agent_config:
            raise Exception('agent config not found')
        agent_executor = self.agent_loader.load_executor(agent_config)
        await agent_executor.cancel(context, event_queue)


def _get_agent(context: RequestContext) -> Tuple[str, str]:
    if not context.call_context:
        raise Exception('context.call_context is none')
    namespace = context.call_context.state["headers"].pop(X_AGENT_NAMESPACE)
    if not namespace:
        raise Exception(f'agent id not found in state {X_AGENT_NAMESPACE}')
    name = context.call_context.state["headers"].pop(X_AGENT_NAME)
    if not name:
        raise Exception(f'agent id not found in state {X_AGENT_NAME}')
    return namespace, name
