import asyncio
from acp_mcp.adapter import Adapter


def cli():
    import argparse

    parser = argparse.ArgumentParser(
        prog="mcp2acp", description="Serve ACP agents over MCP"
    )
    parser.add_argument("url", type=str, help="The URL of an ACP server")

    args = parser.parse_args()

    adapter = Adapter(acp_url=args.url)
    asyncio.run(adapter.serve())


if __name__ == "__main__":
    cli()
