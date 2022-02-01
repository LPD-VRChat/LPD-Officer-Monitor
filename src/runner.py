import os
import sys


def run():
    os.environ.setdefault("LPD_OFFICER_MONITOR_ENVIRONMENT", "dev")

    from src.main import main

    main()


if __name__ == "__main__":
    run()
    os.execv(sys.executable, ["python", "-m", "src.runner"])
