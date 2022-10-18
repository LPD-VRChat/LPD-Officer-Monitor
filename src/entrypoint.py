import sys
import io
import os
import subprocess

# only meant to be used inside docker
#non 0 exit code on failure

try:
    outputB = subprocess.check_output(['alembic', 'current', "-v"])
except subprocess.CalledProcessError as err:
    print("ERROR alembic process", err)
    sys.exit(1)

output = outputB.decode("ascii")

for line in output.splitlines():
    if line.startswith("Rev:"):
        if "(head)" in line:
            break
        else:
            print("ERROR: Migration is probably needed\nAlembic output bellow:\n", output)
            sys.exit(1)
else:
    print("ERROR: Failed to parse alembic output\nAlembic output bellow:\n", output)
    sys.exit(1)

print("INFO: alembic output=", output)
sys.exit(0)