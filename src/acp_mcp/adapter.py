import asyncio
import json
import logging

from acp_sdk.client import Client
from acp_sdk.models import Agent, RunStatus, Message, SessionId, AwaitResume, RunId, Run
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("acp-mcp")


class Adapter:
    def __init__(
        self,
        *,
        acp_url: str,
        refresh_interval: int = 15,
        refresh_timeout: int = 5,
        run_timeout: int = 300,
    ):
        self.acp_url = acp_url
        self.refresh_interval = refresh_interval
        self.refresh_timeout = refresh_timeout
        self.run_timeout = run_timeout

        self._agents: dict[str, Agent] = {}

    async def serve(self):
        server = FastMCP("acp-mcp")

        @server.resource(
            uri=self.acp_url + "/agents",
            name="agents",
            description="List of available agents",
            mime_type="application/json",
        )
        @server.tool(name="list_agents", description="List available agents")
        async def list_agents() -> str:
            return json.dumps([agent.model_dump() for agent in self._agents.values()])

        @server.resource(
            uri=self.acp_url + "/agents/{agent}",
            name="agent",
            description="Information about an agent",
            mime_type="application/json",
        )
        @server.tool(name="get_agent", description="Get information about an agent")
        async def agent(agent: str) -> str:
            return self._find_agent(agent).model_dump_json()

        @server.tool(name="run_agent", description="Runs an agent with given input")
        async def run(agent: str, input: Message, session: SessionId | None = None):
            async with (
                Client(base_url=self.acp_url, timeout=self.run_timeout) as client,
                client.session(session_id=session) as ses,
            ):
                run = await ses.run_sync(input, agent=self._find_agent(agent).name)
            return self._run_to_tool_response(run)

        @server.tool(
            name="resume_run",
            description="Resumes an awaiting agent run",
        )
        async def resume_run(await_resume: AwaitResume, run_id: RunId):
            async with Client(
                base_url=self.acp_url, timeout=self.run_timeout
            ) as client:
                run = await client.run_resume_sync(await_resume, run_id=run_id)
            return self._run_to_tool_response(run)

        refresh = asyncio.create_task(self._refresh_loop())
        try:
            await server.run_stdio_async()
        finally:
            refresh.cancel()
            await refresh

    def _find_agent(self, agent: str):
        if agent not in self._agents:
            raise RuntimeError("Agent not found")
        return self._agents[agent]

    async def _refresh(self):
        async with Client(
            base_url=self.acp_url, timeout=self.refresh_timeout
        ) as client:
            self._agents = {agent.name: agent async for agent in client.agents()}

    async def _refresh_loop(self):
        while True:
            try:
                await self._refresh()
                logger.info("Agents refreshed")
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Agents refresh failed")
            await asyncio.sleep(self.refresh_interval)

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
