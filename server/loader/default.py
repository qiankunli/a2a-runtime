from typing import Dict

from a2a.server.agent_execution import AgentExecutor

from agent.helloworld.agent_executor import HelloWorldAgentExecutor
from agent.travel.travel_executor import TravelExecutor
from agent.weather.weather_executor import WeatherExecutor
from server.common.model import AgentConfig
from server.loader.base import AgentLoader


class DefaultAgentLoader(AgentLoader):
    # todo 后续支持扫描目录自动初始化
    # todo 也可以agent目录实现一个agent后，自动加注解，自动注册
    def __init__(self, ) -> None:
        self._agent_cache: Dict[str, AgentExecutor] = {}

    def load_executor(self, agent_config: AgentConfig) -> AgentExecutor:
        if agent_config.namespace_name in self._agent_cache:
            return self._agent_cache[agent_config.namespace_name]
        if agent_config.namespace_name == 'default/helloworld':
            executor = HelloWorldAgentExecutor()
            self._agent_cache[agent_config.namespace_name] = executor
            return executor
        elif agent_config.namespace_name == 'default/weather':
            executor = WeatherExecutor()
            self._agent_cache[agent_config.namespace_name] = executor
            return executor
        elif agent_config.namespace_name == 'default/travel':
            executor = TravelExecutor()
            self._agent_cache[agent_config.namespace_name] = executor
            return executor

        raise ValueError(f'No agent executor found for agent {agent_config.namespace_name}')
