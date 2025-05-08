import asyncio
import logging
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from importlib.metadata import version

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
from mcp.types import (
    EmbeddedResource,
    ImageContent,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, TypeAdapter

logger = logging.getLogger(__name__)


class RunAgentInput(BaseModel):
    agent: AgentName
    input: list[Message]
    session: SessionId | None = None


class RunAgentResumeInput(BaseModel):
    run: RunId
    await_resume: AwaitResume


class EmptySchema(BaseModel):
    pass


@dataclass
class Context:
    client: Client


def create_adapter(acp_url: AnyHttpUrl) -> Server:
    @asynccontextmanager
    async def lifespan(server: Server) -> AsyncIterator[Context]:
        logger.info("Running server")
        try:
            async with Client(base_url=str(acp_url)) as client:
                yield Context(client=client)
        finally:
            logger.info("Server shutdown")

    server = Server("acp-mcp", version=version("acp-mcp"), lifespan=lifespan)

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        client = server.request_context.lifespan_context.client
        agents = [agent async for agent in client.agents()]
        return [
            Resource(
                uri=_create_agent_uri(acp_url, agent.name),
                name=agent.name,
                description=agent.description,
            )
            for agent in agents
        ]

    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
        agent = _parse_agent_from_url(uri)
        if agent is None:
            raise ValueError("Invalid resource")

        client = server.request_context.lifespan_context.client
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
                inputSchema=EmptySchema.model_json_schema(),
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
        client = server.request_context.lifespan_context.client
        match name:
            case "list_agents":
                return [
                    EmbeddedResource(
                        type="resource",
                        resource=TextResourceContents(
                            uri=_create_agent_uri(acp_url, agent.name),
                            mimeType="application/json",
                            text=agent.model_dump_json(),
                        ),
                    )
                    async for agent in client.agents()
                ]
            case "run_agent":
                try:
                    input = RunAgentInput.model_validate(arguments)
                    async with client.session(session_id=input.session) as session:
                        run = await session.run_sync(input.input, agent=input.agent)
                        return [TextContent(type="text", text=_run_to_tool_text(run))]
                except Exception as e:
                    logger.warning(f"BASE: {client.client.base_url}")
                    logger.warning(f"Caught an exception: {e}\n{traceback.format_exc()}")
            case "resume_run_agent":
                input = RunAgentResumeInput.model_validate(arguments)
                run = await client.run_resume_sync(
                    input.await_resume,
                    run_id=input.run,
                )
                return [TextContent(type="text", text=_run_to_tool_text(run))]
            case _:
                raise ValueError("Invalid tool name")

    return server


def _create_agent_uri(base_url: AnyHttpUrl, agent: AgentName) -> AnyHttpUrl:
    return AnyHttpUrl.build(
        scheme=base_url.scheme,
        username=base_url.username,
        password=base_url.password,
        host=base_url.host,
        port=base_url.port,
        path=(base_url.path.rstrip("/") + f"/agents/{agent}").lstrip("/"),
        query=base_url.query,
        fragment=base_url.fragment,
    )


def _parse_agent_from_url(url: AnyUrl) -> AgentName | None:
    path_segments = url.path.split("/")
    if len(path_segments) < 3 or path_segments[1] != "agents" or len(path_segments[2]) == 0:
        return None
    return path_segments[2]


def _run_to_tool_text(run: Run) -> str:
    "Encodes run into tool response"
    match run.status:
        case RunStatus.AWAITING:
            return f"Run {run.run_id} awaits: {run.await_request.model_dump_json()}"
        case RunStatus.COMPLETED:
            return TypeAdapter(list[Message]).dump_json(run.output).decode()
        case RunStatus.CANCELLED:
            raise asyncio.CancelledError("Agent run cancelled")
        case RunStatus.FAILED:
            raise RuntimeError("Agent failed with error:", run.error)
        case _:
            raise RuntimeError(f"Agent {run.status.value}")
