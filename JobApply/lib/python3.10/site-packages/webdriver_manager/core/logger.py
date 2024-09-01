import logging

from webdriver_manager.core.config import wdm_log_level

__logger = logging.getLogger("WDM")
__logger.addHandler(logging.NullHandler())


def log(text):
    """Emitting the log message."""
    __logger.log(wdm_log_level(), text)


def set_logger(logger):
    """
    Set the global logger.

    Parameters
    ----------
    logger : logging.Logger
        The custom logger to use.

    Returns None
    """

    # Check if the logger is a valid logger
    if not isinstance(logger, logging.Logger):
        raise ValueError("The logger must be an instance of logging.Logger")

    # Bind the logger input to the global logger
    global __logger
    __logger = logger
