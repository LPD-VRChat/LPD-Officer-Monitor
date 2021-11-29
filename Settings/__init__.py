import os as _os

# Import only from base if the program is being unit tests
if _os.environ.get("LPD_OFFICER_MONITOR_UNIT_TESTING"):
    from .base import *
else:
    try:
        # Override with settings for production or development
        if _os.environ.get("LPD_OFFICER_MONITOR_ENVIRONMENT") == "dev":
            from .dev import *
        else:
            from .production import *
    except ImportError:
        pass

    # Override anything except testing settings with the local settings
    try:
        from .local import *
    except ImportError:
        pass
