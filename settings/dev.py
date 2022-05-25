from .base import *
import os as _os
import tracemalloc as _tracemalloc

# fmt: off
# Rank Role Ladder ###############################################

ROLE_LADDER.cadet.id = 666005873679663134
ROLE_LADDER.recruit.id = 594238854102515735
ROLE_LADDER.officer.id = 834215801426018335
ROLE_LADDER.senior_officer.id = 594239040723615780
ROLE_LADDER.corporal.id = 834215092496629771
ROLE_LADDER.sergeant.id = 0
ROLE_LADDER.staff_sergeant.id = 0
ROLE_LADDER.advisor.id = 0
ROLE_LADDER.lieutenant.id = 0
ROLE_LADDER.captain.id = 584111242705371138
ROLE_LADDER.deputy_chief.id = 0
ROLE_LADDER.chief.id = 717803321569837216
# fmt: on

SERVER_ID = 566315650864381953
MAX_INACTIVE_DAYS = 2
MAX_INACTIVE_MSG_DAYS = 1
MIN_ACTIVITY_MINUTES = 1
SLEEP_TIME_BETWEEN_OFFICER_CHECKS = 60

# Channel IDs ####################################################
##### Command channel IDs
ADMIN_BOT_CHANNEL = 566777522252152883
TEAM_BOT_CHANNEL = 774748395972722688
GENERAL_BOT_CHANNEL = 708117281376305232
ALLOWED_COMMAND_CHANNELS = [ADMIN_BOT_CHANNEL, TEAM_BOT_CHANNEL, GENERAL_BOT_CHANNEL]

##### Other channel IDs
ERROR_LOG_CHANNEL = 670751809538752512
LEAVE_OF_ABSENCE_CHANNEL = 734906620630401045
REQUEST_RANK_CHANNEL = 834184946964103178
MOD_LOG_CHANNEL = 938090795775434762

# Role IDs #######################################################
##### Trainer Role IDs
TRAINER_ROLE = 655128037993742337
SLRT_TRAINER_ROLE = 670305215265636386
LMT_TRAINER_ROLE = 773997789939761204
PRISON_TRAINER_ROLE = 820117446672384021

##### Team Role IDs
LPD_ROLE = 655133459714670592
SLRT_TRAINED_ROLE = 670305435332378624
LMT_TRAINED_ROLE = 773997905631248416
WATCH_OFFICER_ROLE = 820117275532066838
PROGRAMMING_TEAM_ROLE = 820416948613152808
DEV_TEAM_ROLE = 746362203225063454
TEAM_LEAD_ROLE = 828430724583129119
EVENT_HOST_ROLE = 768205907770867732
MEDIA_PRODUCTION_ROLE = 820119886113144882
RECRUITER_ROLE = 633018289777410068
JANITOR_ROLE = 820120880117317652
INSTIGATOR_ROLE = 820118440165638174
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
KOREAN_ROLE = 820122312782250024
CHINESE_ROLE = 820122389483356190

##### Moderation Role IDs
MODERATOR_ROLE = 569166391891197964
CHAT_MODERATOR_ROLE = 767437788475162641
DETENTION_ROLE = 767436972804538418
DETENTION_WAITING_AREA_ROLE = 767437105948655666
INACTIVE_ROLE = 590684921534873620

# Category IDs ###################################################
ON_DUTY_CATEGORIES = [599764719212953610]
IGNORED_CATEGORIES = [599764719212953610]

# Database settings ##############################################
DB_NAME = "LPD_Officer_Monitor"
DB_USER = "lpd"
DB_HOST = "localhost"
DB_SOCK = "/run/mysqld/mysqld.sock"
DB_TYPE = "mysql"
DB_PORT = 3306

# Logging ########################################################
LOGGING_WEBHOOK = "https://discord.com/api/webhooks/913832874883575838/qYRBo1a2WHblyk1wXUpURyUNoL9bp4gLZBiItte31sKDLQFSoXFh8eoeqinQjmuwLNCw"
_os.environ.setdefault("PYTHONASYNCIODDEBUG", "1")
_tracemalloc.start()

# Web Manager settings ###########################################
WEB_MANAGER_HOST = "localhost"
