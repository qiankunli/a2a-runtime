import uvicorn

from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
)

from server.a2a2.agent_execution.runtime_agent_executor import RuntimeAgentExecutor
from server.a2a2.apps.jsonrpc.runtime_fastapi_app import RuntimeA2AFastAPIApplication
from server.a2a2.request_handlers.runtime_request_handler import RuntimeRequestHandler
from server.common.model import AgentConfig
from server.conf import settings
from server.config_store.base import AgentConfigStore
from server.config_store.default import DefaultAgentConfigStore
from server.libs.redis.client import RedisConfig
from server.loader.base import AgentLoader
from server.loader.default import DefaultAgentLoader
from server.notifier.base import Notifier
from server.notifier.redis import RedisNotifier


def init_agent_config_store() -> AgentConfigStore:
    # todo 后续改为从配置中加载
    helloworld_agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/default/helloworld',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=[],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )
    hello_agent_config = AgentConfig(
        name='helloworld',
        namespace='default',
        card=helloworld_agent_card.model_dump(),
        extended_card=helloworld_agent_card.model_dump(),
    )

    weather_agent_card = AgentCard(
        name='Weather Agent',
        description='Helps with weather',
        url='http://localhost:9999/default/weather',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=[],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )
    weather_agent_config = AgentConfig(
        name='weather',
        namespace='default',
        card=weather_agent_card.model_dump(),
        extended_card=weather_agent_card.model_dump(),
    )
    travel_agent_card = AgentCard(
        name='travel planner Agent',
        description='travel planner',
        url='http://localhost:9999/default/travel',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=[],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )
    travel_agent_config = AgentConfig(
        name='travel',
        namespace='default',
        card=travel_agent_card.model_dump(),
        extended_card=travel_agent_card.model_dump(),
    )
    return DefaultAgentConfigStore(agent_configs=[hello_agent_config, weather_agent_config, travel_agent_config])


def init_agent_loader() -> AgentLoader:
    # todo 后续改为从配置中加载
    return DefaultAgentLoader()


def init_notifier() -> Notifier | None:
    # todo 后续改为从配置中加载
    if settings.NOTIFIER_TYPE == 'redis':
        return RedisNotifier(RedisConfig.from_settings(), settings.NOTIFIED_REDIS_CHANNEL)
    return None


if __name__ == '__main__':
    # todo 后续可以扩展为super agent 将任务转发给其他agent
    # 先占位
    public_agent_card = AgentCard(
        name='Hello World Agent',
        description='Just a hello world agent',
        url='http://localhost:9999/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[],  # Only the basic skill for the public card
        supports_authenticated_extended_card=True,
    )
    agent_config_store = init_agent_config_store()
    agent_loader = init_agent_loader()
    notifier = init_notifier()
    # todo 有机会试下DatabaseTaskStore
    request_handler = RuntimeRequestHandler(
        agent_executor=RuntimeAgentExecutor(agent_config_store, agent_loader),
        task_store=InMemoryTaskStore(),
    )

    server = RuntimeA2AFastAPIApplication(
        agent_config_store=agent_config_store,
        notifier=notifier,
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(server.build(), host=settings.UVICORN_HOST, port=settings.UVICORN_PORT)
