import pytest

pytest_plugins = [
    "e2e.fixtures.session",
]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
