FROM python:3.9-slim

WORKDIR /app

COPY pyproject.toml poetry.lock .
RUN pip install poetry
RUN poetry install

COPY . .

CMD ["poetry", "run", "python", "src/main.py"]
