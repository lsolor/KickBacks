FROM python:3.12-slim

ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

COPY pyproject.toml .
COPY alembic.ini .
COPY README.md .
COPY kickback ./kickback
COPY migrations ./migrations

RUN uv pip install --system .

EXPOSE 8000

CMD ["uvicorn", "kickback.main:app", "--host", "0.0.0.0", "--port", "8000"]
