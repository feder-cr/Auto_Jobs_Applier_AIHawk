import os
from dotenv import load_dotenv


def str2bool(value):
    return value.lower() in ['true', '1']


load_dotenv()


def ssl_verify():
    return str2bool(os.getenv("WDM_SSL_VERIFY", "true"))


def gh_token():
    return os.getenv("GH_TOKEN", None)


def wdm_local():
    return str2bool(os.getenv("WDM_LOCAL", "false"))


def wdm_log_level():
    default_level = 20
    try:
        return int(os.getenv("WDM_LOG", default_level))
    except Exception:
        return default_level


def wdm_progress_bar():
    default_level = 1
    try:
        return int(os.getenv("WDM_PROGRESS_BAR", default_level))
    except Exception:
        return default_level


def get_xdist_worker_id():
    return os.getenv("PYTEST_XDIST_WORKER", '')
