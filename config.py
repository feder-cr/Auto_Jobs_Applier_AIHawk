# In this file, you can set the configurations of the app.
import constants

# config related to logging must have prefix LOG_
LOG_LEVEL = constants.DEBUG
LOG_SELENIUM_LEVEL = constants.DEBUG
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

MINIMUM_WAIT_TIME_IN_SECONDS = 60

JOB_APPLICATIONS_DIR = "job_applications"
JOB_SUITABILITY_SCORE = 7

JOB_MAX_APPLICATIONS = 5
JOB_MIN_APPLICATIONS = 0

LLM_MODEL_TYPE = constants.OPENAI
LLM_MODEL = "gpt-4o-mini"
LLM_API_URL = "http://localhost:11434"  # Only required for OLLAMA models
