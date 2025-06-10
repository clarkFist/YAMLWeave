import subprocess
import sys
import time

MAX_ATTEMPTS = 100
DELAY_SECONDS = 1


def safe_push(message: str = "更新脚本快速更新") -> None:
    try:
        subprocess.run(["git", "add", "-A"], check=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"])
        has_changes = result.returncode != 0
        if has_changes:
            subprocess.run(["git", "commit", "-m", message], check=True)
        else:
            print("No changes to commit.")
    except subprocess.CalledProcessError as exc:
        print(f"Failed to stage or commit changes: {exc}")
        sys.exit(1)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt} to pull and push changes...")
            subprocess.run(["git", "pull", "--rebase"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("Push successful.")
            return
        except subprocess.CalledProcessError as exc:
            print(f"Push failed on attempt {attempt}: {exc}")
            time.sleep(DELAY_SECONDS)
    print("All push attempts failed.")
    sys.exit(1)


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "更新脚本快速更新"
    safe_push(msg)
