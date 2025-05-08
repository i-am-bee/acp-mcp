import pytest
from acp_sdk.models import AgentName
from pydantic import AnyHttpUrl

from acp_mcp.adapter import _create_agent_uri, _parse_agent_from_url


@pytest.mark.parametrize(
    "base,agent,expected",
    [
        (AnyHttpUrl("http://localhost:8000"), "foobar", AnyHttpUrl("http://localhost:8000/agents/foobar")),
        (AnyHttpUrl("http://localhost:8000/"), "foobar", AnyHttpUrl("http://localhost:8000/agents/foobar")),
        (
            AnyHttpUrl("http://localhost:8000/v1/acp"),
            "foobar",
            AnyHttpUrl("http://localhost:8000/v1/acp/agents/foobar"),
        ),
    ],
)
def test_create_agent_uri(base: AnyHttpUrl, agent: AgentName, expected: AnyHttpUrl) -> None:
    assert _create_agent_uri(base, agent) == expected


@pytest.mark.parametrize(
    "agent_uri,expected",
    [
        (AnyHttpUrl("http://localhost:8000/agents/foobar"), "foobar"),
        (AnyHttpUrl("http://localhost:8000/agents/"), None),
        (AnyHttpUrl("http://localhost:8000"), None),
        (AnyHttpUrl("http://localhost:8000/tools/foobat"), None),
        (AnyHttpUrl("http://localhost:8000/v1/acp/agents/foobar"), "foobar"),
    ],
)
def test_parse_agent_from_url(agent_uri: AnyHttpUrl, expected: AgentName) -> None:
    assert _parse_agent_from_url(agent_uri) == expected
