FROM python:3.7-slim

ARG ZVT_USERNAME
ARG ZVT_PASSWORD
ARG ZVT_HOST
ARG ZVT_PORT
ARG ZVT_DB

ENV PYTHONPATH=/application \
    MAX_WORKERS=1 \
    ZVT_USERNAME=$ZVT_USERNAME \
    ZVT_PASSWORD=$ZVT_PASSWORD \
    ZVT_HOST=$ZVT_HOST \
    ZVT_PORT=$ZVT_PORT \
    ZVT_DB=$ZVT_DB

WORKDIR /application

# Install dependencies
RUN apt-get update \
    && apt-get -y --no-install-recommends install gcc libmariadb-dev-compat libmariadb-dev \
    && pip install poetry "uvicorn[standard]" gunicorn --no-cache-dir \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Install zvt
RUN python -c "from zvt.api import *"; exit 0
RUN echo "{\"data_path\": \"/root/zvt-home/data\"," > /root/zvt-home/config.json \
    "\"db_engine\": \"mysql\"," >> /root/zvt-home/config.json \
    "\"mysql_username\": \"$ZVT_USERNAME\"," >> /root/zvt-home/config.json \
    "\"mysql_password\": \"$ZVT_PASSWORD\"," >> /root/zvt-home/config.json \
    "\"mysql_server_address\": \"$ZVT_HOST\"," >> /root/zvt-home/config.json \
    "\"mysql_server_port\": $ZVT_PORT," >> /root/zvt-home/config.json \
    "\"db_name\": \"$ZVT_DB\"}" >> /root/zvt-home/config.json

# Copy files
COPY ./app ./app

COPY ./scripts/start.sh .
RUN chmod +x ./start.sh

COPY ./conf/gunicorn_conf.py .

CMD ["./start.sh"]
