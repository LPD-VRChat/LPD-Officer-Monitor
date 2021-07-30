import os as _os


try:
    if _os.environ.get("LPD_OFFICER_MONITOR_ENVIRONMENT") == "dev":
        from .dev import *
    else:
        from .production import *
except ImportError:
    pass

try:
    from .local import *
except ImportError:
    pass
