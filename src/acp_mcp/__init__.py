import asyncio
from acp_mcp.server import serve


def cli():
    import argparse

    parser = argparse.ArgumentParser(
        prog="mcp2acp", description="Serve ACP agents over MCP"
    )
    parser.add_argument("url", type=str, help="The URL of an ACP server")

    args = parser.parse_args()

    asyncio.run(serve(acp_url=args.url))


if __name__ == "__main__":
    cli()
