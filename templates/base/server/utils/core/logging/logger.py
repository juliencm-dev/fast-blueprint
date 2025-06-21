from typing import override
import atexit
import logging.config
import logging.handlers
import yaml
import json
from pathlib import Path
import datetime as dt

logger = logging.getLogger(__name__)

DEFAULT_LOG_ATTRS={ 
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}

def setup_logger():
    config = Path(__file__).parent / "log_config.yml"
    with open(config) as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler != None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


class JSONFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys else {}
    
    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._format_message_to_dict(record)
        return json.dumps(message, default=str)

    def _format_message_to_dict(self, record: logging.LogRecord) -> dict[str, str]:
        always_keys = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }

        if record.exc_info:
            always_keys["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            always_keys["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: value
            if (value := always_keys.get(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        } 

        message.update(always_keys)

        for key, value in record.__dict__.items():
            if key not in DEFAULT_LOG_ATTRS:
                message[key] = value
        return message 









