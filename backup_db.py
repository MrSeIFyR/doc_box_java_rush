import os
import subprocess
from datetime import datetime
from pathlib import Path
import logging

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

logger = logging.getLogger("docbox.backup")
logger.setLevel(logging.INFO)
logger.handlers.clear()

file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(name)s]")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

DB_NAME = "docbox_db"
DB_USER = "postgres"
DB_PASSWORD = "password"

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
backup_file = BACKUP_DIR / f"backup_{timestamp}.sql"

logger.info("Starting backup process for DB=%s", DB_NAME)

try:
    result = subprocess.run(
        ["docker", "compose", "ps", "-q", "db"],
        capture_output=True,
        text=True,
        check=True
    )
    db_container = result.stdout.strip()
    if not db_container:
        raise RuntimeError("Container 'db' not found")
    logger.info("Container db found: %s", db_container)

    cmd = ["docker", "exec", "-t", db_container, "pg_dump", "-U", DB_USER, DB_NAME]
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    with open(backup_file, "w", encoding="utf-8") as f:
        subprocess.run(cmd, env=env, stdout=f, check=True)

    logger.info("Backup completed successfully: %s", backup_file)
    print(f"🎉 Бэкап успешно создан: {backup_file}")

except subprocess.CalledProcessError as e:
    msg = f"Backup failed (exit code {e.returncode}): {e.stderr.strip()}"
    logger.error(msg, exc_info=True)
    print("❌ Ошибка при создании бэкапа:", msg)
    exit(1)
except Exception as e:
    msg = f"Unexpected error during backup: {e}"
    logger.exception(msg)
    print("❌ Неожиданная ошибка:", msg)
    exit(1)