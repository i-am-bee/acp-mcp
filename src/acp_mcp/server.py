from acp_sdk.client import Client
from acp_sdk.models import Agent, RunStatus, Message, SessionId
from mcp.server.fastmcp import FastMCP


async def serve(acp_url: str) -> None:
    server = FastMCP("acp-mcp")

    async with Client(base_url=acp_url) as client:

        @server.tool(name="run_agent", description="Runs an agent with given input")
        async def run_agent(
            agent: str, input: Message, session: SessionId | None = None
        ) -> list[Message]:
            async with client.session(session_id=session) as ses:
                run = await ses.run_sync(input, agent=agent)
            match run.status:
                case RunStatus.COMPLETED:
                    return run.output
                case RunStatus.FAILED:
                    raise RuntimeError("Agent failed with error:", run.error)
                case _:
                    raise RuntimeError(f"Agent {run.status.value}")

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
