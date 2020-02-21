LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "level": "INFO",
            "formatter": "default",
        },
        "errors": {
            "class": "logging.FileHandler",
            "filename": "qbot-errors.log",
            "mode": "w",
            "level": "ERROR",
            "formatter": "default",
        },
    },
    "root": {"level": "INFO", "handlers": ["console", "errors"]},
}
