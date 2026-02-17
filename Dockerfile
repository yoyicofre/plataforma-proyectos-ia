FROM python:3.11-slim

WORKDIR /app

# System deps (si luego agregas psycopg u otras libs nativas, amplía esto)
RUN pip install --no-cache-dir -U pip

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY scripts /app/scripts

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
