# syntax=docker/dockerfile:1

#FROM python:latest #1.7GB
FROM python:3.10-alpine
USER root
WORKDIR /app

# RUN apk update
# RUN apk add --no-cache git gcc g++ musl-dev mariadb-connector-c-dev ffmpeg

# # Install requirements
COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt

# #clean up
# RUN pip cache purge
# RUN apk del -r git gcc g++ musl-dev mariadb-connector-c-dev
# RUN rm -rf /var/cache/apk/*
# RUN rm -rf /root/.cache/pip/*

#doing everything in one command to reduce layer
RUN apk update && \
    apk add --no-cache git gcc g++ musl-dev mariadb-connector-c-dev ffmpeg && \
    pip install -r requirements.txt && \
    pip cache purge && \
    apk del -r git gcc g++ musl-dev mariadb-connector-c-dev && \
    rm -rf /var/cache/apk/* && \
    rm -rf /root/.cache/pip/*

#run as user instead of running bot as root
RUN addgroup -S swuser && \
    adduser -H -S swuser -G swuser
USER swuser

# Run the app
# COPY . . #commented out to allow reload
ENV LPD_OFFICER_MONITOR_DOCKER=1
ENTRYPOINT [ "./docker-entrypoint.sh" ]
CMD [ "python", "-u", "-m", "src.runner" ]
