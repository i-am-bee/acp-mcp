import pytest
from mcp import ClientSession
from mcp.types import TextContent

from e2e.config import Config

mock_agents = [
    f"http://localhost:{Config.PORT}/agents/echo",
    f"http://localhost:{Config.PORT}/agents/slow_echo",
]


@pytest.mark.asyncio
async def test_list_tools(session: ClientSession) -> None:
    expected_tool_names = ["list_agents", "run_agent", "resume_run_agent"]

    result = await session.list_tools()
    tool_names = [tool.name for tool in result.tools]

    for name in expected_tool_names:
        assert name in tool_names


@pytest.mark.asyncio
async def test_list_agents(session: ClientSession) -> None:
    result = await session.call_tool("list_agents")
    assert not result.isError
    assert len(result.content) == len(mock_agents)


@pytest.mark.asyncio
async def test_run_agent(session: ClientSession) -> None:
    result = await session.call_tool("run_agent", {"agent": "echo", "input": [{"parts": [{"content": "Howdy!"}]}]})
    assert not result.isError
    assert isinstance(result.content[0], TextContent)
