# scripts/watchdog.py
"""
Process Monitor (Watchdog) for AI Employee
Monitors critical AI processes (orchestrator, watchers) and restarts them if they fail.
"""
import subprocess
import time
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WATCHDOG - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent.parent / 'vault' / 'Logs' / 'watchdog.log')
    ]
)
logger = logging.getLogger(__name__)

# Processes to monitor (modify as needed)
PROCESSES_TO_WATCH = {
    'orchestrator': ['python', str(Path(__file__).parent.parent / 'orchestrator.py')],
    # 'gmail_watcher': ['python', 'path/to/watchers/gmail_watcher.py'],
}

active_processes = {}

def start_process(name, cmd):
    logger.info(f"Starting process: {name}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        active_processes[name] = proc
        return proc
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        return None

def check_and_restart():
    for name, cmd in PROCESSES_TO_WATCH.items():
        proc = active_processes.get(name)
        
        # If it doesn't exist or has terminated
        if proc is None or proc.poll() is not None:
            if proc is not None:
                # Log exit codes and errors if it crashed
                exit_code = proc.poll()
                logger.warning(f"Process {name} terminated with exit code {exit_code}. Restarting...")
                stdout, stderr = proc.communicate()
                if stderr:
                    logger.error(f"Captured stderr for {name}:\n{stderr}")
            else:
                logger.info(f"Process {name} not running. Initializing...")
                
            start_process(name, cmd)

if __name__ == "__main__":
    logger.info("Initializing AI Employee Watchdog Process Manager...")
    # Ensure Logs directory exists
    Path(Path(__file__).parent.parent / 'vault' / 'Logs').mkdir(parents=True, exist_ok=True)
    
    try:
        while True:
            check_and_restart()
            time.sleep(30) # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("Watchdog shutting down. Terminating managed processes...")
        for name, proc in active_processes.items():
            proc.terminate()
            proc.wait()
        logger.info("All processes terminated cleanly.")
