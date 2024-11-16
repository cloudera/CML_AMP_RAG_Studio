import logging


def setup_logger(
    name: str,
    log_level: int = logging.INFO,
) -> logging.Logger:
    # Create a logger object
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Create a formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
