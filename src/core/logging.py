import logging
import os
import sys
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    """Configura logging base.

    - Safe-by-default: salida a stdout, formato legible.
    - Se puede controlar con env var LOG_LEVEL.

    Nota: si necesitan JSON logs, se reemplaza el formatter en este módulo.
    """
    lvl = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=lvl,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "app")
