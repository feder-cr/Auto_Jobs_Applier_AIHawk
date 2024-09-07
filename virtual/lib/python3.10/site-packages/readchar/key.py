# flake8: noqa E401,E403
# this file exists only for backwards compatibility
# it allows the use of `import readchar.key`
import sys

from . import key as __key


for __k, __v in vars(__key).items():
    if not __k.startswith("__"):
        setattr(sys.modules[__name__], __k, __v)
