import asyncio

from acp_sdk.client import Client
from acp_sdk.models import Agent, RunStatus, Message, SessionId, AwaitResume, RunId, Run
from mcp.server.fastmcp import FastMCP


def run_to_tool_response(run: Run):
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


async def serve(acp_url: str) -> None:
    server = FastMCP("acp-mcp")

    async with Client(base_url=acp_url) as client:

        @server.tool(name="run_agent", description="Runs an agent with given input")
        async def run(agent: str, input: Message, session: SessionId | None = None):
            async with client.session(session_id=session) as ses:
                run = await ses.run_sync(input, agent=agent)
            return run_to_tool_response(run)

        @server.tool(
            name="resume_run",
            description="Resumes an awaiting agent run",
        )
        async def resume_run(await_resume: AwaitResume, run_id: RunId):
            run = await client.run_resume_sync(await_resume, run_id=run_id)
            return run_to_tool_response(run)

        def register_agent(agent: Agent) -> None:
            @server.resource(
                uri=f"acp://agents/{agent.name}",
                name=agent.name,
                description=agent.description,
                mime_type="application/json",
            )
            async def read_agent() -> str:
                return agent.model_dump_json()

        async for agent in client.agents():
            register_agent(agent)

        await server.run_stdio_async()
