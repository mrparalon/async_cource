SHELL := /bin/bash

CMD:=poetry run

py_warn = PYTHONDEVMODE=1

migrate:
	alembic upgrade head

make_migrations:
	alembic revision --autogenerate -m "$(name)"

run:
	uvicorn --reload --proxy-headers "src.main:app"

check:
	${CMD} ruff check . || (echo "Please run 'make format' to auto-fix import style issues" && exit 1) && \
	${CMD} black --check . || (echo "Please run 'make format' to auto-fix code style issues" && exit 1) && \
	${CMD} pyright || exit 1;

format:
	ruff check --fix .;
	black .;

test:
	pytest
