# LPD-Officer-Monitor
This repository stores a discord bot made for the VRChat role-play group Loli Police Department to monitor the activity of LPD Officers.

This branch contains the development version of V3. It is structured very differently, and as such, maintenance will be vastly different.

## Requirements

- Git
- python 3.10+ (only outside docker)
- docker (optional)
- MySql/MariaDB server


## Setup for DEV

create virtual environement
```
python3 -m venv .venv
```

Reinstall requirements
```
pip install -r requirements.txt
```
## Database update

create/upgrade the tables. Base need to exists
```
alembic upgrade head
````

Generate a migration from the difference between the database model revision and the current model
```
alembic revision --autogenerate -m "Added voiceChannel"
```

## Docker

### Notes
The bot isn't going to do database operation (creation, migration) automatically, you need to do it by hand, Refer to `Maintenance` section.

The image is using Alpine for now to be as light as possible, any distribution could be used.

Python venv isn't used in Docker

### Download

First checkout
```sh
git clone --branch v3-main https://github.com/LPD-VRChat/LPD-Officer-Monitor.git
```

update only:
```sh
git pull
```

### Setup

generate random password for db
```
cat /dev/urandom | tr -dc A-Za-z0-9 | head -c 64 > mysql_root_password
cat /dev/urandom | tr -dc A-Za-z0-9 | head -c 64 > mysql_user_password
```
you will need 2 additional file named `discord_token` and `discord_secret`

Build the images used by the container, sometimes `Dockerfile` changes are not picked up and this need to be executed before `up`
```
docker compose build
```

Launch
```
docker compose up -d
```

### Maintenance / Database operation
If the entrypoint fails, you need to create an empty file named `keepalive` in this folder. Once maintenance is done you can delete and container should stop.

Create/upgrade the tables. Base need to exists (should be created by the db container)
```
alembic upgrade head
````