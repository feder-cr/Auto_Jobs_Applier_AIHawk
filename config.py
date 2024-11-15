# In this file, you can set the configurations of the app.
import constants  # Do not import individual constants - this adds tech debt

# config related to logging must have prefix LOG_
LOG_LEVEL = constants.DEBUG
LOG_SELENIUM_LEVEL = constants.DEBUG
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

MINIMUM_WAIT_TIME_IN_SECONDS = 60

# Recommendations for max applicants based on the time filter
MAX_APPLICATIONS_DAY = 50
MAX_APPLICATIONS_WEEK = 150
MAX_APPLICATIONS_MONTH = 400
MAX_APPLICATIONS_ALLTIME = 600
MAX_APPLICATIONS_CUSTOM = 5  # Change based on needs

JOB_APPLICATIONS_DIR = "job_applications"
JOB_SUITABILITY_SCORE = 7

JOB_MAX_APPLICATIONS = MAX_APPLICATIONS_DAY  # Change based on "date" in work preferences or use custom
JOB_MIN_APPLICATIONS = 0

LLM_MODEL_TYPE = constants.OPENAI
LLM_MODEL = "gpt-4o-mini"
LLM_API_URL = "http://localhost:11434"  # Only required for OLLAMA models
