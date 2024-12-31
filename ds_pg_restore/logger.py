import logging
import logging.config


def setup_logging() -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(levelname)s %(name)s %(filename)s"
                    " %(lineno)s %(process)d %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                    "rename_fields": {
                        "levelname": "level",
                        "asctime": "timestamp",
                        "name": "logger",
                    },
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "root": {"level": "INFO", "handlers": ["stdout"]},
            },
        }
    )
    logging.captureWarnings(True)


def get_logger() -> logging.Logger:
    return logging.getLogger("ds_pg_restore")
