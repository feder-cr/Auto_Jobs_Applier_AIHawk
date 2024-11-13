# In this file, you can set the configurations of the app.

from constants import DEBUG, LLM_MODEL, OPENAI

#config related to logging must have prefix LOG_
LOG_LEVEL = DEBUG
LOG_SELENIUM_LEVEL = DEBUG
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

MINIMUM_WAIT_TIME_IN_SECONDS = 60

JOB_APPLICATIONS_DIR = "job_applications"
JOB_SUITABILITY_SCORE = 7

JOB_MAX_APPLICATIONS = 5
JOB_MIN_APPLICATIONS = 1

LLM_MODEL_TYPE = 'openai'
LLM_MODEL = 'gpt-4o-mini'
# Only required for OLLAMA models
LLM_API_URL = ''