# Setup the settings default value
import os

os.environ.setdefault("LPD_OFFICER_MONITOR_SETTINGS", "Settings.dev")

import Settings

print(Settings.X_CHANNEL)
