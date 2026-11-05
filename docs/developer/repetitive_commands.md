.venv\Scripts\python.exe -m ruff check . --fix
.venv\Scripts\python.exe -m ruff format
.venv\Scripts\python.exe -m mypy src
.venv\Scripts\python.exe -m pytest -q


# Code quality
.venv\Scripts\python.exe -m ruff check . --fix
.venv\Scripts\python.exe -m ruff format
.venv\Scripts\python.exe -m mypy src

# Automated tests
.venv\Scripts\python.exe -m pytest -q

# Coverage
.venv\Scripts\python.exe -m coverage run -m pytest
.venv\Scripts\python.exe -m coverage report
