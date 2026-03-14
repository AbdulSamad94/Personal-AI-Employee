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

WATCHER_DONE_DIR = Path(__file__).parent / "watchers" / "done"
WATCHER_TODO_DIR = Path(__file__).parent / "watchers" / "todo"


def start_watcher(script_name):
    script_path = WATCHER_DONE_DIR / script_name
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return None

    return subprocess.Popen([sys.executable, str(script_path)])


def main():
    watchers = {}
    done_scripts = [
        "gmail_watcher.py",
        "linkedin_watcher.py",
        "filesystem_watcher.py",  # Watchdog event-driven Inbox watcher
        "approval_watcher.py",  # Approved → Action dispatcher
    ]
    todo_scripts = []

    print("\n--- AI Employee Orchestrator ---")

    # Start all done watchers
    for script in done_scripts:
        proc = start_watcher(script)
        if proc:
            watchers[script] = proc
            print(f"[OK] {script.replace('.py', '')} - running (PID: {proc.pid})")
        else:
            print(f"[FAIL] {script.replace('.py', '')} - failed to start")

    # Note todo watchers
    for script in todo_scripts:
        print(f"[TODO] {script.replace('.py', '')} - not built yet")

    print("---------------------------------\n")

    try:
        while True:
            for name, proc in watchers.items():
                if proc.poll() is not None:
                    logging.warning(
                        f"Watcher {name} crashed (Exit code: {proc.returncode}). Restarting..."
                    )
                    watchers[name] = start_watcher(name)
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Shutting down orchestrator...")
        for proc in watchers.values():
            proc.terminate()


if __name__ == "__main__":
    main()
