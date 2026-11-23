FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    RADAR_DB_PATH=/data/jobs.db \
    RADAR_PROFILE=/config/profile.yaml

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY radar ./radar
COPY profile.example.yaml .

RUN useradd --system --uid 10001 radar \
    && mkdir -p /data /config \
    && chown radar /data
USER radar

VOLUME ["/data"]

ENTRYPOINT ["python", "-m", "radar"]
CMD ["run", "--send"]
