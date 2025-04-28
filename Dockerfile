FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv sync

CMD ["uv", "run", "python", "server.py", "${ACP_URL}"]
