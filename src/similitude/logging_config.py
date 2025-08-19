# Licensed under the Apache License, Version 2.0
import logging
import os

def setup_logging() -> None:
    level_name = os.getenv("SIM_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt)
