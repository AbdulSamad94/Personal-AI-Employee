import os
import subprocess
import time
import logging
import sys
from pathlib import Path

# Setup logging
VAULT = Path(__file__).parent / "vault"
LOGS = VAULT / "Logs"
LOGS.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "orchestrator.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

WATCHERS_DIR = Path(__file__).parent / "watchers"


def start_watcher(script_name, extra_env=None):
    script_path = WATCHERS_DIR / script_name
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return None

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.Popen([sys.executable, str(script_path)], env=env)


def main():
    watchers = {}
    # (script_name, display_name, extra_env) — display_name must be unique even
    # when the same script is launched multiple times (e.g. one gmail_watcher.py
    # process per Gmail account), since it's used as the watchers dict key.
    watcher_configs = [
        ("gmail_watcher.py", "gmail_watcher (personal)", {"GMAIL_ACCOUNT_LABEL": "default"}),
        ("gmail_watcher.py", "gmail_watcher (work)", {"GMAIL_ACCOUNT_LABEL": "work"}),
        ("linkedin_watcher.py", "linkedin_watcher", None),
        ("filesystem_watcher.py", "filesystem_watcher", None),  # Watchdog event-driven Inbox watcher
        ("approval_watcher.py", "approval_watcher", None),  # Approved → Action dispatcher
        ("telegram_approval_watcher.py", "telegram_approval_watcher", None),  # Pending_Approval → Telegram ping
        ("discord_approval_watcher.py", "discord_approval_watcher", None),  # Pending_Approval → Discord ping (redundant channel, Telegram is intermittently blocked in Pakistan)
    ]

    print("\n--- AI Employee Orchestrator ---")

    for script, name, env in watcher_configs:
        proc = start_watcher(script, env)
        if proc:
            watchers[name] = (script, env, proc)
            print(f"[OK] {name} - running (PID: {proc.pid})")
        else:
            print(f"[FAIL] {name} - failed to start")

    print("---------------------------------\n")

    try:
        while True:
            for name, (script, env, proc) in list(watchers.items()):
                if proc.poll() is not None:
                    logging.warning(
                        f"Watcher {name} crashed (Exit code: {proc.returncode}). Restarting..."
                    )
                    watchers[name] = (script, env, start_watcher(script, env))
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Shutting down orchestrator...")
        for _, _, proc in watchers.values():
            proc.terminate()


if __name__ == "__main__":
    main()
