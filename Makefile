SRC = app scripts tests

.PHONY: server debug test flake8 mypy script

default:
	@echo "帮助:"
	@echo "\tmake server            启动服务器"
	@echo "\tmake debug             启动调试服务器"
	@echo "\tmake test              启动测试"
	@echo "\tmake script            执行脚本"
	@echo "\tmake flake8            启动Flake8"
	@echo "\tmake mypy              启动mypy"

server:
	. .env && poetry run uvicorn app.main:app --host=$$DYNACONF_PT_HOST --port=$$DYNACONF_PT_PORT

debug:
	. .env && poetry run uvicorn app.main:app --host=$$DYNACONF_PT_HOST --port=$$DYNACONF_PT_PORT --reload --debug

test:
	. .env && poetry run pytest --cov=app --cov=tests --cov-report=term-missing --cov-report html

flake8:
	poetry run flake8 $(SRC)

mypy:
	mypy app

script:
	export PYTHONPATH=. & poetry run python ./scripts/cli.py $(filter-out $@,$(MAKECMDGOALS))

