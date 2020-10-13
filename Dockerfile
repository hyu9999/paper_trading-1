FROM python:3.7-buster

WORKDIR /paper_trading

COPY ./app app
COPY ./tests tests
COPY ./Makefile ./
COPY ./pyproject.toml ./poetry.lock* ./

# Install Poetry and package
RUN pip install poetry \
    && poetry cache clear pypi --all \
    && poetry update \
    && poetry install --no-dev

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

CMD ["poetry", "run", "uvicorn", "app.main:app"]