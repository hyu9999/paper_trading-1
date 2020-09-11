.PHONY: initdb

default:
	@echo "帮助:"
	@echo "\tmake initdb 初始化数据库"

initdb:
	poetry run sh -c "PYTHONPATH=. python ./scripts/db_tools.py initdb"