FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /paper_trading

COPY ./app app
COPY ./tests tests
COPY ./Makefile ./
COPY ./pyproject.toml ./poetry.lock* ./

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

RUN poetry install

COPY ./app app