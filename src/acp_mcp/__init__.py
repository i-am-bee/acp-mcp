import asyncio
import logging

from pydantic import AnyHttpUrl

from acp_mcp.adapter import create_adapter, serve


def cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="mcp2acp", description="Serve ACP agents over MCP")
    parser.add_argument("url", type=AnyHttpUrl, help="The URL of an ACP server")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout for the ACP client, in seconds",
    )

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    server = create_adapter(acp_url=args.url, timeout=args.timeout)
    asyncio.run(serve(server, "stdio"))


if __name__ == "__main__":
    cli()
