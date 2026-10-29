.venv\Scripts\python.exe -m ruff check . --fix
.venv\Scripts\python.exe -m ruff format
.venv\Scripts\python.exe -m mypy src
.venv\Scripts\python.exe -m pytest -q
