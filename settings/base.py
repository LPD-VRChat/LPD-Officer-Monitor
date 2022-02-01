from .classes import RoleLadderElement, RoleLadder
import os as _os
from enum import Enum

PROJECT_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

# fmt: off
# Rank Role Ladder ###############################################
ROLE_LADDER = RoleLadder(
    cadet = RoleLadderElement("LPD Cadet", "cadet", 666005873679663134),
    recruit = RoleLadderElement("LPD Recruit", "recruit", 594238854102515735),
    officer = RoleLadderElement("LPD Officer", "officer", 834215801426018335),
    senior_officer = RoleLadderElement("LPD Senior Officer", "senior_officer", 594239040723615780),
    corporal = RoleLadderElement("LPD Corporal", "corporal", 834215092496629771, False),
    sergeant = RoleLadderElement("LPD Sergeant", "sergeant", 645394647350247465, False),
    staff_sergeant = RoleLadderElement("LPD Staff Sergeant", "staff_sergeant", 711366388186480751, False, True),
    advisor = RoleLadderElement("LPD Advisor", "advisor", 679474638266433567, False, True),
    lieutenant = RoleLadderElement("LPD Lieutenant", "lieutenant", 645394607714074634, False, True),
    captain = RoleLadderElement("LPD Captain", "captain", 645394574055047198, False, True),
    deputy_chief = RoleLadderElement("LPD Deputy Chief", "deputy_chief", 645394500717641751, False, True, True),
    chief = RoleLadderElement("LPD Chief", "chief", 645388308158873610, False, True, True),
)
# fmt: on

SERVER_ID = 645383380870889482
MAX_INACTIVE_DAYS = 56
MAX_INACTIVE_MSG_DAYS = 14
MIN_ACTIVITY_MINUTES = 60
SLEEP_TIME_BETWEEN_OFFICER_CHECKS = 3600

# Channel IDs ####################################################
##### Command channel IDs
ADMIN_BOT_CHANNEL = 645383848284258305
TEAM_BOT_CHANNEL = 774740277235154975
GENERAL_BOT_CHANNEL = 708736137463726131
ALLOWED_COMMAND_CHANNELS = [ADMIN_BOT_CHANNEL, TEAM_BOT_CHANNEL, GENERAL_BOT_CHANNEL]

##### Other channel IDs
ERROR_LOG_CHANNEL = 677546865998168144
LEAVE_OF_ABSENCE_CHANNEL = 725110720722894869
REQUEST_RANK_CHANNEL = 655570475216535585

# Role IDs #######################################################
##### Trainer Role IDs
TRAINER_ROLE = 664258877161279096
SLRT_TRAINER_ROLE = 663137582317568001
LMT_TRAINER_ROLE = 684866780283666518
PRISON_TRAINER_ROLE = 802721606912180294

##### Team Role IDs
LPD_ROLE = 654438235950415902
SLRT_TRAINED_ROLE = 665996573981016103
LMT_TRAINED_ROLE = 759780133556453386
WATCH_OFFICER_ROLE = 802721610603298836
PROGRAMMING_TEAM_ROLE = 730149646130741258
DEV_TEAM_ROLE = 645751942626279460
TEAM_LEAD_ROLE = 767181875960610837
EVENT_HOST_ROLE = 647216389886705684
MEDIA_PRODUCTION_ROLE = 645680788934754365
RECRUITER_ROLE = 655632175168749600
JANITOR_ROLE = 730835142322421791
INSTIGATOR_ROLE = 780172087733125181
TEAMS = {
    "Programming Team": PROGRAMMING_TEAM_ROLE,
    "Dev Team": DEV_TEAM_ROLE,
    "Event Host Team": EVENT_HOST_ROLE,
    "Media Production Team": MEDIA_PRODUCTION_ROLE,
    "Instigation Team": INSTIGATOR_ROLE,
}

TRAINER_TEAMS = {
    "Trainer Team": TRAINER_ROLE,
    "SLRT Trainer Team": SLRT_TRAINER_ROLE,
    "LMT Trainer Team": LMT_TRAINER_ROLE,
    "Prison Trainer Team": PRISON_TRAINER_ROLE,
}

TEAMS.update(TRAINER_TEAMS)


##### Language Role IDs
KOREAN_ROLE = 738499962412859393
CHINESE_ROLE = 738500383860588574

##### Moderation Role IDs
MODERATOR_ROLE = 654458435785588737
CHAT_MODERATOR_ROLE = 751164515177201776
DETENTION_ROLE = 645401830561546250
DETENTION_WAITING_AREA_ROLE = 697914340870848533
INACTIVE_ROLE = 765299198148476979

# Category IDs ###################################################
ON_DUTY_CATEGORY = 645392700257992728
IGNORED_CATEGORIES = [
    696352449228832778,
    645390444691456020,
    647218270411292694,
    658094796413599754,
]

# Database settings ##############################################
DB_NAME = "LPD_Officer_Monitor"
DB_USER = "lpd"
DB_HOST = "localhost"
DB_SOCK = "/run/mysqld/mysqld.sock"
DB_TYPE = "mysql"
DB_PORT = 3306

# The password for the MySQL database
DB_PASS = "AVerySecurePasswordIndeed"

# General settings ###############################################
BOT_PREFIX = "="
DB_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NAME_SEPARATOR = ";"
LOG_FILE_PATH = _os.path.join(PROJECT_DIR, "logs", "lpd_officer_monitor.log")

# Logging ########################################################
LOGGING_WEBHOOK = "INSERT_WEBHOOK_HERE"
_os.environ.setdefault("PYTHONASYNCIODDEBUG", "0")

# Web Manager settings ###########################################
WEB_MANAGER_PORT = 443
WEB_MANAGER_HOST = "0.0.0.0"

# The certfile and keyfile for the bot's SSL certificate
CERTFILE = "certs/cert.pem"
KEYFILE = "certs/key.pem"

# Change this in local and keep it very secret
WEB_SECRET_KEY = b"TheSecretKeyForWebSecret"

# Discord OAuth credentials ######################################
DISCORD_TOKEN = "yigbuq3cfr98by7wvefgrt78b9ywv34t8ib7uiybgw3f4ubigycuvifuv4uigy"
CLIENT_ID = 0
CLIENT_SECRET = "wg43tgw4gw4gwgyhsae54ty35y35"
CALLBACK_URL = "https://callback.url"