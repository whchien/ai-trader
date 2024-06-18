import json
import logging
import time
from typing import Any, Dict

log_file_name = f"log/log_{time.time()}"
logging.basicConfig(filename=log_file_name)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def log_telemetry(logger_instance: logging.Logger, tags: [Dict, Any]) -> None:
    assert tags.get("event") is not None, "Must pass a event name."

    logger_instance.info("json:%s", json.dumps(tags), stacklevel=2)
