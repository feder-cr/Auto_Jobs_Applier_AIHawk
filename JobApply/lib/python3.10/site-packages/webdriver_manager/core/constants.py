import os
import sys

ROOT_FOLDER_NAME = ".wdm"
DEFAULT_PROJECT_ROOT_CACHE_PATH = os.path.join(sys.path[0], ROOT_FOLDER_NAME)
DEFAULT_USER_HOME_CACHE_PATH = os.path.join(
    os.path.expanduser("~"), ROOT_FOLDER_NAME)
