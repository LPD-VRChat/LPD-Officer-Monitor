import os as _os
import configparser


def _readSecretFile(name: str) -> str:
    filepath = name
    if not name.startswith("/"):
        filepath = f"Keys/{name}"
    with open(filepath, "r") as f:
        return f.read()


def _readDockerSecret(envKey: str) -> str:
    envVar = _os.environ.get(envKey)
    assert envVar, f"{envKey} is not defined"
    return _readSecretFile(envVar)


CONFIG_LOADED = "None"

# Import only from base if the program is being unit tests
if _os.environ.get("LPD_OFFICER_MONITOR_UNIT_TESTING"):
    from .base import *

    CONFIG_LOADED = "base_test"
else:
    try:
        # Override with settings for production or development
        if _os.environ.get("LPD_OFFICER_MONITOR_ENVIRONMENT") == "dev":
            from .dev import *

            CONFIG_LOADED = "dev"
        else:
            from .production import *

            CONFIG_LOADED = "prod"
    except ImportError:
        CONFIG_LOADED = "err"
        pass

    # Override anything except testing settings with the local settings
    try:
        from .local import *
    except ImportError:
        pass

    if _os.environ.get("LPD_OFFICER_MONITOR_DOCKER"):
        DB_HOST = "db"
        DB_NAME = "LPD_Officer_Monitor_v3"
        DB_USER = "lpdbot"
        DB_PASS = _readDockerSecret("MYSQL_PASSWORD_FILE")
        DISCORD_TOKEN = _readDockerSecret("DISCORD_TOKEN_FILE")
        LOG_FILE_PATH = "/logs/lpd_officer_monitor.log"


## ini land for saving local settings
iniconfig = configparser.ConfigParser()

_LOCAL_INI_PATH = _os.path.dirname(__file__) + _os.sep + "local.ini"


def save_ini():
    global iniconfig
    with open(_LOCAL_INI_PATH, "w") as f:
        iniconfig.write(f)


def load_ini():
    global iniconfig
    iniconfig.read(_LOCAL_INI_PATH)
    # Ensure sections exist
    if "VRC" not in iniconfig:
        iniconfig["VRC"] = {}
        save_ini()


load_ini()
