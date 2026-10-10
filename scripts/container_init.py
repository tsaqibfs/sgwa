"""Prepare the container database and local ML model before serving traffic."""
import subprocess
import sys


def main():
    commands = [
        ["alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        ["ml.train"],
        ["backend.app.seed"],
        ["scripts.backfill_results"],
    ]
    for command in commands:
        print(f"Initializing: {command[0]}", flush=True)
        subprocess.run([sys.executable, "-m", *command], check=True)


if __name__ == "__main__":
    main()
