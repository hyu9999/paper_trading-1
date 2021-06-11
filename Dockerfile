FROM python:3.7-slim

ENV PYTHONPATH=/application \
    MAX_WORKERS=1

WORKDIR /application

# Install dependencies
RUN apt-get update \
    && apt-get -y --no-install-recommends install gcc libmariadb-dev-compat libmariadb-dev \
    && pip install poetry "uvicorn[standard]" gunicorn --no-cache-dir \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy files
COPY ./app ./app
ADD /conf/zvt-config.json /root/zvt-home/config.json

COPY ./scripts/start.sh .
RUN chmod +x ./start.sh

COPY ./conf/gunicorn_conf.py .

CMD ["./start.sh"]
