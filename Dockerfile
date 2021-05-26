FROM python:3.7-slim

ENV PYTHONPATH=/application \
    MAX_WORKERS=1

WORKDIR /application

# Install dependencies
RUN apt-get update \
    && pip install poetry "uvicorn[standard]" gunicorn --no-cache-dir \
    && apt-get clean autoclean \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /var/cache/apt/archives/*.deb


COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy files
COPY ./app ./app

COPY ./scripts/start.sh .
RUN chmod +x ./start.sh

COPY ./conf/gunicorn_conf.py .

CMD ["./start.sh"]
