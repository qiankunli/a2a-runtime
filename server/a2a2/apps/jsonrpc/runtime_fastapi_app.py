import asyncio
import logging

from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from a2a.server.apps import CallContextBuilder, JSONRPCApplication
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.types import (
    A2ARequest,
    AgentCard,
)
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    DEFAULT_RPC_URL,
    EXTENDED_AGENT_CARD_PATH,
    PREV_AGENT_CARD_WELL_KNOWN_PATH,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from server.common.model import X_AGENT_NAME, X_AGENT_NAMESPACE
from server.conf import settings
from server.config_store.base import AgentConfigStore
from server.notifier.base import Notifier

logger = logging.getLogger(__name__)


class RuntimeA2AFastAPIApplication(JSONRPCApplication):
    def __init__(
            self,
            agent_config_store: AgentConfigStore,
            notifier: Notifier | None,
            agent_card: AgentCard,
            http_handler: RequestHandler,
            extended_agent_card: AgentCard | None = None,
            context_builder: CallContextBuilder | None = None,
            card_modifier: Callable[[AgentCard], AgentCard] | None = None,
            extended_card_modifier: Callable[[AgentCard, ServerCallContext], AgentCard] | None = None,
    ) -> None:
        super().__init__(
            agent_card, http_handler, extended_agent_card, context_builder, card_modifier, extended_card_modifier
        )
        self.agent_config_store = agent_config_store
        self.notifier = notifier

    def add_routes_to_app(
            self,
            app: FastAPI,
            agent_card_url: str = AGENT_CARD_WELL_KNOWN_PATH,
            rpc_url: str = DEFAULT_RPC_URL,
            extended_agent_card_url: str = EXTENDED_AGENT_CARD_PATH,
    ) -> None:
        app.get('')(self.list_agents)
        app.get('/')(self.list_agents)
        agent_rpc_url = f'/{{namespace}}/{{name}}{rpc_url}'
        app.post(
            agent_rpc_url,
            openapi_extra={
                'requestBody': {
                    'content': {'application/json': {'schema': {'$ref': '#/components/schemas/A2ARequest'}}},
                    'required': True,
                    'description': 'A2ARequest',
                }
            },
        )(self.handle_requests)
        if agent_rpc_url.endswith('/'):
            agent_rpc_url_without_slash = agent_rpc_url.removesuffix('/')
            app.post(
                agent_rpc_url_without_slash,
                openapi_extra={
                    'requestBody': {
                        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/A2ARequest'}}},
                        'required': True,
                        'description': 'A2ARequest',
                    }
                },
            )(self.handle_requests)
        app.get(f'/{{namespace}}/{{name}}{agent_card_url}')(self.handle_get_agent_card)

        if agent_card_url == AGENT_CARD_WELL_KNOWN_PATH:
            # For backward compatibility, serve the agent card at the deprecated path as well.
            # TODO: remove in a future release
            app.get(f'/{{namespace}}/{{name}}{PREV_AGENT_CARD_WELL_KNOWN_PATH}')(self.handle_get_agent_card)

        if self.agent_card.supports_authenticated_extended_card:
            app.get(f'/{{namespace}}/{{name}}{extended_agent_card_url}')(
                self.handle_get_authenticated_extended_agent_card
            )

    async def handle_requests(
            self,
            request: Request,
            namespace: str,
            name: str,
    ) -> Response:
        # 便于下游链路识别agent id，参见 DefaultCallContextBuilder
        request.scope['headers'].append((X_AGENT_NAMESPACE.encode(), namespace.encode()))
        request.scope['headers'].append((X_AGENT_NAME.encode(), name.encode()))
        return await self._handle_requests(request)

    async def handle_get_agent_card(
            self,
            namespace: str,
            name: str,
    ) -> JSONResponse:
        agent_config = await self.agent_config_store.get(namespace, name)
        card_to_serve = agent_config.get_card()
        if self.card_modifier:
            card_to_serve = self.card_modifier(card_to_serve)

        return JSONResponse(
            card_to_serve.model_dump(
                exclude_none=True,
                by_alias=True,
            )
        )

    async def handle_get_authenticated_extended_agent_card(
            self,
            request: Request,
            namespace: str,
            name: str,
    ) -> JSONResponse:
        logger.warning(
            'HTTP GET for authenticated extended card has been called by a client. '
            'This endpoint is deprecated in favor of agent/authenticatedExtendedCard '
            'JSON-RPC method and will be removed in a future release.'
        )
        if not self.agent_card.supports_authenticated_extended_card:
            return JSONResponse(
                {'error': 'Extended agent card not supported or not enabled.'},
                status_code=404,
            )
        agent_config = await self.agent_config_store.get(namespace, name)
        card_to_serve = agent_config.get_extended_card()

        if self.extended_card_modifier:
            context = self._context_builder.build(request)
            # If no base extended card is provided, pass the public card to the modifier
            base_card = card_to_serve if card_to_serve else self.agent_card
            card_to_serve = self.extended_card_modifier(base_card, context)

        if card_to_serve:
            return JSONResponse(
                card_to_serve.model_dump(
                    exclude_none=True,
                    by_alias=True,
                )
            )
        # If supports_authenticated_extended_card is true, but no
        # extended_agent_card was provided, and no modifier produced a card,
        # return a 404.
        return JSONResponse(
            {'error': 'Authenticated extended agent card is supported but not configured on the server.'},
            status_code=404,
        )

    async def list_agents(self) -> JSONResponse:
        agent_configs = await self.agent_config_store.list()
        serialized_configs = [agent_config.model_dump(exclude_none=True) for agent_config in agent_configs]
        return JSONResponse(content=serialized_configs)

    async def sync_agent_config(
            self,
    ):
        async for agent_config in await self.notifier.watch():
            logger.debug(f'sync agent config {agent_config}')
            await self.agent_config_store.sync_agent_config(agent_config)

    async def reload_agent_config(
            self,
    ):
        logger.info('reload agent config')
        await self.agent_config_store.reload()

    def build(
            self,
            agent_card_url: str = AGENT_CARD_WELL_KNOWN_PATH,
            rpc_url: str = DEFAULT_RPC_URL,
            extended_agent_card_url: str = EXTENDED_AGENT_CARD_PATH,
            **kwargs: Any,
    ) -> FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            a2a_request_schema = A2ARequest.model_json_schema(ref_template='#/components/schemas/{model}')
            defs = a2a_request_schema.pop('$defs', {})
            openapi_schema = app.openapi()
            component_schemas = openapi_schema.setdefault('components', {}).setdefault('schemas', {})
            component_schemas.update(defs)
            component_schemas['A2ARequest'] = a2a_request_schema

            if settings.CONFIG_RELOAD_INTERVAL_SECONDS > 0:
                scheduler = AsyncIOScheduler()
                scheduler.add_job(
                    self.reload_agent_config,
                    IntervalTrigger(seconds=settings.CONFIG_RELOAD_INTERVAL_SECONDS),
                    id='reload_agent_config',
                    max_instances=1,
                    coalesce=False,
                    replace_existing=True,
                )
            # create sync config task
            if self.notifier:
                asyncio.create_task(self.sync_agent_config())
            yield

        app = FastAPI(lifespan=lifespan, redoc_url='/redocs', **kwargs)
        self.add_routes_to_app(app, agent_card_url, rpc_url, extended_agent_card_url)

        return app
