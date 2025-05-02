import pytest
from mcp import ClientSession

from e2e.config import Config

mock_agents = [
    f"http://localhost:{Config.PORT}/agents/echo",
    f"http://localhost:{Config.PORT}/agents/slow_echo",
]


@pytest.mark.anyio
async def test_list_agents(session: ClientSession) -> None:
    result = await session.list_resources()
    resource_uris = [str(resource.uri) for resource in result.resources]

    for agent in mock_agents:
        assert agent in resource_uris


@pytest.mark.anyio
@pytest.mark.parametrize(
    "agent",
    mock_agents,
)
async def test_read_agent(session: ClientSession, agent: str) -> None:
    result = await session.read_resource(agent)
    assert str(result.contents[0].uri) == agent
