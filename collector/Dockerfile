FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY collector ./collector
RUN pip install --no-cache-dir -e .

ENV ROOMBA_DB_PATH=/data/roomba.db
VOLUME /data

CMD ["python", "-m", "collector.main"]
