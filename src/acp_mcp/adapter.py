import asyncio
import logging

from acp_sdk.client import Client
from acp_sdk.models import (
    AgentName,
    AwaitResume,
    Message,
    Run,
    RunId,
    RunStatus,
    SessionId,
)
from mcp.server import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmbeddedResource,
    ImageContent,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)
from pydantic import AnyUrl, BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("acp-mcp")


class RunAgentInput(BaseModel):
    agent: AgentName
    input: Message
    session: SessionId | None = None


class RunAgentResumeInput(BaseModel):
    run: RunId
    await_resume: AwaitResume


class Adapter:
    def __init__(self, *, acp_url: str, timeout: int = 300) -> None:
        self.acp_url = acp_url
        self.timeout = timeout

    async def serve(self, server: Server | None = None) -> None:
        server = server or Server("acp-mcp")

        @server.list_resources()
        async def list_resources() -> list[Resource]:
            async with Client(base_url=self.acp_url, timeout=self.timeout) as client:
                agents = [agent async for agent in client.agents()]
                return [
                    Resource(
                        uri=self._create_agent_uri(agent.name),
                        name=agent.name,
                        description=agent.description,
                    )
                    for agent in agents
                ]

        @server.read_resource()
        async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
            agent = self._parse_agent_from_uri(uri)
            if agent is None:
                raise ValueError("Invalid resource")
            async with Client(base_url=self.acp_url, timeout=self.timeout) as client:
                agent = await client.agent(name=agent)
                return [
                    ReadResourceContents(
                        mime_type="application/json",
                        content=agent.model_dump_json(),
                    )
                ]

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="list_agents",
                    description="Lists available agents",
                    inputSchema={},
                ),
                Tool(
                    name="run_agent",
                    description="Runs an agent",
                    inputSchema=RunAgentInput.model_json_schema(),
                ),
                Tool(
                    name="resume_run_agent",
                    description="Resumes an agent run",
                    inputSchema=RunAgentResumeInput.model_json_schema(),
                ),
            ]

        @server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict | None
        ) -> list[TextContent | ImageContent | EmbeddedResource]:
            async with Client(base_url=self.acp_url, timeout=self.timeout) as client:
                match name:
                    case "list_agents":
                        return [
                            EmbeddedResource(
                                type="resource",
                                resource=TextResourceContents(
                                    uri=self._create_agent_uri(agent.name),
                                    mimeType="application/json",
                                    text=agent.model_dump_json(),
                                ),
                            )
                            async for agent in client.agents()
                        ]
                    case "run_agent":
                        input = RunAgentInput.model_validate(arguments)
                        async with client.session(session_id=input.session) as session:
                            run = await session.run_sync(input, agent=input.agent)
                            return self._run_to_tool_response(run)
                    case "resume_run_agent":
                        input = RunAgentResumeInput.model_validate(arguments)
                        run = await client.run_resume_sync(
                            input.await_resume,
                            run_id=input.run,
                        )
                        return self._run_to_tool_response(run)
                    case _:
                        raise ValueError("Invalid tool name")

        async with stdio_server() as (read, write):
            await server.run(
                read,
                write,
                initialization_options=InitializationOptions(
                    server_name=server.name,
                    server_version=server.version,
                    capabilities=server.get_capabilities(),
                ),
            )

    def _create_agent_uri(self, agent: AgentName):
        return f"{self.acp_url}/agents/{agent}"

    def _parse_agent_from_uri(self, uri: AnyUrl) -> AgentName | None:
        path_segments = uri.path.split("/")
        if len(path_segments) < 3 or path_segments[1] != "agents":
            return None
        return path_segments[2]

    def _run_to_tool_response(self, run: Run):
        "Encodes run into tool response"
        match run.status:
            case RunStatus.AWAITING:
                return (f"Run {run.run_id} awaits:", run.await_request)
            case RunStatus.COMPLETED:
                return run.output
            case RunStatus.CANCELLED:
                raise asyncio.CancelledError("Agent run cancelled")
            case RunStatus.FAILED:
                raise RuntimeError("Agent failed with error:", run.error)
            case _:
                raise RuntimeError(f"Agent {run.status.value}")
