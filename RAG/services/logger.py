import logging
import json
import os

LOG_FILE = "logs.txt"

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        return json.dumps(log_record, ensure_ascii=False)


def get_logger(name="rag_logger"):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # éviter duplication

    logger.setLevel(logging.INFO)

    # Handler fichier
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())

    logger.addHandler(file_handler)

    return logger