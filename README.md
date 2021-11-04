# LPD-Officer-Monitor
This repository stores a discord bot made for the VRChat role-play group Loli Police Department to monitor the activity of LPD Officers.

This branch contains the development version of V3. It is structured very differently, and as such, maintenance will be vastly different.



## using alembic

create virtual environement
```
python3 -m venv .venv
```

Reinstall requirements
```
pip install -r requirements.txt
```

create/upgrade the tables. Base need to exists
```
alembic upgrade head
````

Generate a migration from the difference between the database model revision and the current model
```
alembic revision --autogenerate -m "Added voiceChannel"
```