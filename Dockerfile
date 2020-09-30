FROM ubuntu:latest
FROM mongo:latest

WORKDIR /paper_trading

COPY ./app app
COPY ./tests tests
COPY ./Makefile ./
COPY ./pyproject.toml ./poetry.lock* ./

# Install Pip
RUN apt-get update && apt-get install -y libzmq3-dev python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip3 install poetry \
    && poetry config virtualenvs.create false

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

RUN poetry install
