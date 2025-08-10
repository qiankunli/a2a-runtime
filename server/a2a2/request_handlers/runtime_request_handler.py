import asyncio
import logging

from typing import cast

from a2a.server.agent_execution import (
    AgentExecutor,
    RequestContextBuilder,
)
from a2a.server.context import ServerCallContext
from a2a.server.events import (
    EventQueue,
    QueueManager,
)
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import (
    PushNotificationConfigStore,
    PushNotificationSender,
    ResultAggregator,
    TaskManager,
    TaskStore,
)
from a2a.types import (
    InvalidParamsError,
    MessageSendParams,
    Task,
    TaskState,
)
from a2a.utils.errors import ServerError
from a2a.utils.telemetry import SpanKind, trace_class

logger = logging.getLogger(__name__)

TERMINAL_TASK_STATES = {
    TaskState.completed,
    TaskState.canceled,
    TaskState.failed,
    TaskState.rejected,
}


@trace_class(kind=SpanKind.SERVER)
class RuntimeRequestHandler(DefaultRequestHandler):

    def __init__(
            self,
            agent_executor: AgentExecutor,
            task_store: TaskStore,
            queue_manager: QueueManager | None = None,
            push_config_store: PushNotificationConfigStore | None = None,
            push_sender: PushNotificationSender | None = None,
            request_context_builder: RequestContextBuilder | None = None,
    ) -> None:
        super().__init__(agent_executor, task_store, queue_manager, push_config_store, push_sender,
                         request_context_builder)

    async def _setup_message_execution(
            self,
            params: MessageSendParams,
            context: ServerCallContext | None = None,
    ) -> tuple[TaskManager, str, EventQueue, ResultAggregator, asyncio.Task]:
        """Common setup logic for both streaming and non-streaming message handling.

        Returns:
            A tuple of (task_manager, task_id, queue, result_aggregator, producer_task)
        """
        # Create task manager and validate existing task
        task_manager = TaskManager(
            task_id=params.message.task_id,
            context_id=params.message.context_id,
            task_store=self.task_store,
            initial_message=params.message,
        )
        task: Task | None = await task_manager.get_task()

        if task:
            if task.status.state in TERMINAL_TASK_STATES:
                raise ServerError(
                    error=InvalidParamsError(
                        message=f'Task {task.id} is in terminal state: {task.status.state}'
                    )
                )

            task = task_manager.update_with_message(params.message, task)
        elif params.message.task_id:
            # diff with DefaultRequestHandler
            # 如果是新message，使用上游推荐的task_id，便于上游关联数据
            pass
            # raise ServerError(
            #     error=TaskNotFoundError(
            #         message=f'Task {params.message.task_id} was specified but does not exist'
            #     )
            # )

        # Build request context
        request_context = await self._request_context_builder.build(
            params=params,
            task_id=task.id if task else params.message.task_id,
            context_id=params.message.context_id,
            task=task,
            context=context,
        )

        task_id = cast('str', request_context.task_id)
        # Always assign a task ID. We may not actually upgrade to a task, but
        # dictating the task ID at this layer is useful for tracking running
        # agents.

        if (
                self._push_config_store
                and params.configuration
                and params.configuration.push_notification_config
        ):
            await self._push_config_store.set_info(
                task_id, params.configuration.push_notification_config
            )

        queue = await self._queue_manager.create_or_tap(task_id)
        result_aggregator = ResultAggregator(task_manager)
        # TODO: to manage the non-blocking flows.
        producer_task = asyncio.create_task(
            self._run_event_stream(request_context, queue)
        )
        await self._register_producer(task_id, producer_task)

        return task_manager, task_id, queue, result_aggregator, producer_task

