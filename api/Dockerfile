FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY api ./api
RUN pip install --no-cache-dir -e .

ENV ROOMBA_DB_PATH=/data/roomba.db
VOLUME /data
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
