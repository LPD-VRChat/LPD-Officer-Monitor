import os as _os

if _os.environ.get("LPD_OFFICER_MONITOR_SETTINGS") == "Settings.dev":
    from .dev import *
else:
    from .production import *

try:
    from .local import *
except ImportError:
    pass
