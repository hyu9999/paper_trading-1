SRC = app scripts tests

.PHONY: server debug test initdb flake8 mypy

default:
	@echo "帮助:"
	@echo "\tmake server    启动服务器"
	@echo "\tmake debug     启动调试服务器"
	@echo "\tmake test      启动测试"
	@echo "\tmake initdb    初始化数据库"
	@echo "\tmake flake8    启动Flake8"
	@echo "\tmake mypy      启动mypy"

server:
	source .env && poetry run uvicorn app.main:app --host=$$DYNACONF_PT_HOST --port=$$DYNACONF_PT_PORT

debug:
	source .env && poetry run uvicorn app.main:app --host=$$DYNACONF_PT_HOST --port=$$DYNACONF_PT_PORT --reload --debug

test:
	source .env && poetry run pytest --cov=app --cov=tests --cov-report=term-missing --cov-report html

flake8:
	poetry run flake8 $(SRC)

mypy:
	mypy app

initdb:
	poetry run sh -c "PYTHONPATH=. python ./scripts/db_tools.py initdb"