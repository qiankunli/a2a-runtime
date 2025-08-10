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


class WeatherExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent for weather."""

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ):
        # Run the agent until either complete or the task is suspended.
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        print(context.message.parts[0])
        # Immediately notify that the task is submitted.
        if context.message.parts[0].root.kind == 'text':
            if "上海" not in context.message.parts[0].root.text:
                await updater.update_status(TaskState.input_required, message=new_agent_text_message("你问哪里的天气"))
                return
            await updater.update_status(TaskState.completed, message=new_agent_text_message("上海天气很热"))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        pass
