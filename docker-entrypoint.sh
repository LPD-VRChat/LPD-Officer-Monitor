#!/usr/bin/env sh

if eval "python3 src/entrypoint.py"; then
    echo "entrypoint success"
else
    echo "entrypoint failure!!!"
    echo "Create 'keepalive' file to attach to container"
    #sleep 10
    while [ -e keepalive ]
    do
        sleep 1
    done
    exit 1
fi

exec python -u -m src.runner
