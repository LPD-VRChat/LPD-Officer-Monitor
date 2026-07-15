# Requirements

- Git
- Python 3.11
- [Poetry](https://python-poetry.org/docs/#installation)
- MySql/MariaDB server

# Install

## Raw/dev

- Clone this repository
- [Install poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
- Run `poetry install`
    - for dev, run `poetry install --extras dev`
    - if you have multiple python versions installed, you can run `poetry env use 3.10` to use the correct version
- Create a bot token in discord dev portal and setup your `settings/local.py` with it

### Database update

Create your local database.
```sql
sudo mysql
CREATE DATABASE LPD_Officer_Monitor DEFAULT CHARACTER SET UTF8MB4;
CREATE USER lpd@localhost IDENTIFIED BY 'passwordblablabla';
GRANT ALL PRIVILEGES ON LPD_Officer_Monitor.* TO lpd@localhost;
FLUSH PRIVILEGES;
```

Create/upgrade the tables.
```
alembic upgrade head
```

Generate a migration from the difference between the database model revision and the current model
```
alembic revision --autogenerate -m "Added voiceChannel"
```

## Docker

### Notes
The bot isn't going to do database operation (creation, migration) automatically, you need to do it by hand, Refer to `Maintenance` section.

The image is using Alpine for now to be as light as possible, any distribution could be used.

### Setup

generate random password for db
```
cat /dev/urandom | tr -dc A-Za-z0-9 | head -c 64 > mysql_root_password
cat /dev/urandom | tr -dc A-Za-z0-9 | head -c 64 > mysql_user_password
```
you will need 2 additional file named `discord_token`

Build the images used by the container, sometimes `Dockerfile` changes are not picked up and this need to be executed before `up`
```
docker compose build
mkdir logs
sudo chmod a+w logs
```

execute commands inside the python environement to setup de DB
```
docker compose run --rm --entrypoint sh lpd-officer-monitor
```
Refer to next section `Database operation`


### Maintenance / Database operation

If the entrypoint fails, you need to create an empty file named `keepalive` in this folder. Once maintenance is done you can delete and container should stop.

Create/upgrade the tables. Base need to exists (should be created by the db container)
```
alembic upgrade head
````
