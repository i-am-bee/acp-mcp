FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv sync

CMD ["uv", "run", "serve", "$ACP_URL"]
