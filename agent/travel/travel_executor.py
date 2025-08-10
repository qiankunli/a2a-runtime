import logging

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    TaskState,
)
from a2a.utils import new_agent_text_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TravelExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent for weather."""

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.update_status(TaskState.completed,
                                    message=new_agent_text_message("先去故宫，再去长城，再去颐和园"))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        pass
