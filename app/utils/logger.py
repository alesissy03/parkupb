"""
Configurarea sistemului de loguri.

TODO (Task 1 / infrastructură):
- Configurează logging în logs/app.log folosind modulul logging.
- Setează formatul mesajelor (timestamp, nivel, modul etc.).
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging(app):
    # TODO (Task 1): implementează configurarea log-urilor aici
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=3
        )
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    app.logger.handlers = logger.handlers