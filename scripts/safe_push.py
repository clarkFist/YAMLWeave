import subprocess
import sys
import time

MAX_ATTEMPTS = 100
DELAY_SECONDS = 1


def safe_push():
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt} to push changes...")
            subprocess.run(["git", "push"], check=True)
            print("Push successful.")
            return
        except subprocess.CalledProcessError as exc:
            print(f"Push failed on attempt {attempt}: {exc}")
            time.sleep(DELAY_SECONDS)
    print("All push attempts failed.")
    sys.exit(1)


if __name__ == "__main__":
    safe_push()
