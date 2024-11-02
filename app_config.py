# In this file, you can set the configurations of the app.

from constants import DEBUG, LOG_TO_CONSOLE, LOG_TO_FILE, MINIMUM_LOG_LEVEL

LOG_CONFIG = {
    MINIMUM_LOG_LEVEL: DEBUG,
    LOG_TO_FILE: True,
    LOG_TO_CONSOLE: True
}

MINIMUM_WAIT_TIME = 60
