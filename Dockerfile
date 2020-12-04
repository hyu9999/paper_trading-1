FROM python:3.7-buster

EXPOSE 5000
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat vim && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY poetry.lock pyproject.toml ./
RUN pip install poetry==1.1 && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-dev

COPY . ./

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

CMD poetry run uvicorn --host=0.0.0.0 app.main:app
