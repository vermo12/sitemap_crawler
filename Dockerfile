ARG PYTHON_VERSION=3.12.1

FROM python:${PYTHON_VERSION}-bullseye as builder

RUN pip install poetry==1.7.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

FROM python:${PYTHON_VERSION}-slim-bullseye as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY sitemap_crawler ./sitemap_crawler

RUN mkdir out

EXPOSE 8000

CMD ["uvicorn", "sitemap_crawler.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
