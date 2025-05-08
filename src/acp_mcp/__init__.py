import asyncio
import logging

from mcp import stdio_server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from pydantic import AnyHttpUrl

from acp_mcp.adapter import create_adapter

logger = logging.getLogger(__name__)


async def serve(acp_url: AnyHttpUrl) -> None:
    server = create_adapter(acp_url=acp_url)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=server.name,
                server_version=server.version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(), experimental_capabilities={}
                ),
            ),
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="acp-mcp", description="Serve ACP agents over MCP")
    parser.add_argument("url", type=AnyHttpUrl, help="The URL of an ACP server")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    asyncio.run(serve(acp_url=args.url))


if __name__ == "__main__":
    main()
