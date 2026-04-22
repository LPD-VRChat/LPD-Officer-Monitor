# syntax=docker/dockerfile:1


FROM python:3.11-alpine as base
USER root
WORKDIR /app

ARG BUILD_TYPE=prod

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apk update && \
    apk add --no-cache git gcc g++ musl-dev && \
    rm -rf /var/cache/apk/* && \
    rm -rf /root/.cache/pip/*


#poetry builder
FROM base as builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apk update && \
    apk add musl-dev build-base gcc gfortran openblas-dev

WORKDIR /app

RUN pip install poetry

# Install the app
COPY pyproject.toml poetry.lock ./
RUN ls /app
RUN mkdir ${VIRTUAL_ENV}
RUN if [ "${BUILD_TYPE}" = "dev" ]; then \
      poetry install --extras dev --no-root -vvv && rm -rf $POETRY_CACHE_DIR; \
    else \
      poetry install --no-root -vvv && rm -rf $POETRY_CACHE_DIR; \
    fi


FROM base as runtime

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

#COPY src ./src

WORKDIR /app

#run as user instead of running bot as root
RUN addgroup -S swuser && \
    adduser -H -S swuser -G swuser
USER swuser

# Run the app
# COPY . . #commented out to allow reload
ENV LPD_OFFICER_MONITOR_DOCKER=1
ENTRYPOINT [ "./docker-entrypoint.sh" ]
CMD [ "python", "-u", "-m", "src.runner" ]
