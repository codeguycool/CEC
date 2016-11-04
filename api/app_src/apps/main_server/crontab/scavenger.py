"""Background task/thread
Purpose: Remove the unused files
"""

# std
import datetime
import os
import time

# app module
from framework.sys_const import LOG_INFORMATIONAL, LOG_WARNING
from framework.sys_tools import log
from lib.app_const import FILE_CACHE_PATH
from lib.app_var import ADDONS_CACHE_EXPIRE_TIME


def clear_addons_cache():
    """ Clear expire cache addon files.
    """
    now_time = time.time()
    for file_name in os.listdir(FILE_CACHE_PATH):
        if file_name.endswith('.addon'):
            try:
                file_path = os.path.join(FILE_CACHE_PATH, file_name)

                if os.path.isfile(file_path):
                    atime = os.path.getatime(file_path)  # Take access time.

                    if now_time - atime > ADDONS_CACHE_EXPIRE_TIME:
                        log.send(LOG_INFORMATIONAL, 'Delete addon file %s/%s (Last access time: %s)' % (
                            FILE_CACHE_PATH,
                            file_name,
                            datetime.datetime.fromtimestamp(atime).strftime('%Y-%m-%d %H:%M:%S')
                        ))
                        os.remove(file_path)
            except Exception, e:
                log.send(LOG_WARNING, str(e), traceback=True)
                continue
