.PHONY: server debug test initdb

default:
	@echo "帮助:"
	@echo "\tmake server    启动服务器"
	@echo "\tmake debug     启动调试服务器"
	@echo "\tmake test      启动测试"
	@echo "\tmake initdb    初始化数据库"

server:
	source .env && poetry run uvicorn app.main:app --host=$$DYNACONF_PT_HOST --port=$$DYNACONF_PT_PORT

debug:
	source .env && poetry run uvicorn app.main:app --host=$$DYNACONF_PT_HOST --port=$$DYNACONF_PT_PORT --reload --debug

test:
	source .env && poetry run pytest

initdb:
	poetry run sh -c "PYTHONPATH=. python ./scripts/db_tools.py initdb"