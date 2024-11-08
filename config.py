# In this file, you can set the configurations of the app.

from constants import DEBUG
from src.webdrivers.base_browser import BrowserType

#config related to logging must have prefix LOG_
LOG_LEVEL = DEBUG
LOG_SELENIUM_LEVEL = DEBUG
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

MINIMUM_WAIT_TIME_IN_SECONDS = 60

JOB_APPLICATIONS_DIR = "job_applications"
JOB_SUITABILITY_SCORE = 7
BROWSER_TYPE_CONFIG = BrowserType.CHROME
