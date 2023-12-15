FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN  apt-get update
RUN apt-get install python3-dev libpq-dev gcc -y

RUN pip install --upgrade pip
RUN pip install poetry

WORKDIR /app
COPY poetry.lock /app/
COPY pyproject.toml /app/

RUN poetry config virtualenvs.create false
RUN poetry --version
RUN poetry config installer.modern-installation false
RUN poetry install --no-interaction --no-ansi --no-root

COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

COPY bot /app/bot

CMD ["sh", "-c", "export MODE='prod' && alembic upgrade head && python -m bot"]
