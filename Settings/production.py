# fmt: off
# Rank Role Ladder ###############################################

ROLE_LADDER.cadet.id = 663138744588566532
ROLE_LADDER.recruit.id = 645394827025842196
ROLE_LADDER.officer.id = 645394785267482624
ROLE_LADDER.senior_officer.id = 759455978495148062
ROLE_LADDER.corporal.id = 645394678409330688
ROLE_LADDER.sergeant.id = 645394647350247465
ROLE_LADDER.staff_sergeant.id = 711366388186480751
ROLE_LADDER.advisor.id = 679474638266433567
ROLE_LADDER.lieutenant.id = 645394607714074634
ROLE_LADDER.captain.id = 645394574055047198
ROLE_LADDER.deputy_chief.id = 645394500717641751
ROLE_LADDER.chief.id = 645388308158873610
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
    "Trainer Team": TRAINER_ROLE,
    "SLRT Trainer Team": SLRT_TRAINER_ROLE,
    "LMT Trainer Team": LMT_TRAINER_ROLE,
    "Prison Trainer Team": PRISON_TRAINER_ROLE,
    "Programming Team": PROGRAMMING_TEAM_ROLE,
    "Dev Team": DEV_TEAM_ROLE,
    "Event Host Team": EVENT_HOST_ROLE,
    "Media Production Team": MEDIA_PRODUCTION_ROLE,
    "Instigation Team": INSTIGATOR_ROLE,
}

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
