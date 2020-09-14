HOST="127.0.0.1"
PORT=8000
TEST_PATH=./

.PHONY: server debug initdb

default:
	@echo "帮助:"
	@echo "\tmake server 启动服务器"
	@echo "\tmake debug  启动调试服务器"
	@echo "\tmake initdb 初始化数据库"

server:
	poetry run uvicorn app.main:app --host=$(HOST) --port=$(PORT)

debug:
	poetry run uvicorn app.main:app --host=$(HOST) --port=$(PORT) --reload --debug

initdb:
	poetry run sh -c "PYTHONPATH=. python ./scripts/db_tools.py initdb"