# -*-coding: utf-8 -*-
'''System Tools
'''
import cherrypy
import inspect
import subprocess
import threading
import traceback as _traceback

# app module
from framework.py_utilities import Singleton
from framework.sys_var import LOG_LEVEL
from framework.sys_const import LOG_LEVEL_STRING, LOG_ERROR, LOG_DEBUG


class log(object):
    '''Log class
    '''
    @classmethod
    def send(cls, log_level, msg, traceback=False):
        if log_level <= LOG_LEVEL:
            pre_frame = inspect.currentframe().f_back
            pre_frame_info = inspect.getframeinfo(pre_frame)

            log_msg = '{0} {4} (In {1}, Function {2}, Line {3})'.format(LOG_LEVEL_STRING[log_level], pre_frame_info.filename, pre_frame_info.function, pre_frame_info.lineno, msg)
            if traceback:
                err_str = _traceback.format_exc()
                log_msg = '%s\n%s' % (log_msg, err_str)
            cherrypy.log(log_msg)

    @classmethod
    def logging_lock(cls, lock_inst):
        ''' Debug tool. Logging for lock access action.
        Args:
            lock_inst: instance of lock (which has acquire and release method).

        Return:
            instance of lock
        '''
        if LOG_DEBUG > LOG_LEVEL:
            return lock_inst

        def logging(msg):
            pre_frame = inspect.currentframe().f_back.f_back
            pre_frame_info = inspect.getframeinfo(pre_frame)
            nowthread = threading.current_thread().__class__.__name__
            cherrypy.log('{0} {4}: {5} (In {1}, Function {2}, Line {3})'.format(LOG_LEVEL_STRING[LOG_DEBUG], pre_frame_info.filename, pre_frame_info.function, pre_frame_info.lineno, nowthread, msg))

        if hasattr(lock_inst, 'acquire'):
            acquireInst = lock_inst.acquire

            def acquire(blocking=1):
                logging('acquire (lock:%s)' % id(lock_inst))
                ret = acquireInst(blocking)
                logging('acquire sucess (lock:%s)' % id(lock_inst))
                return ret

            lock_inst.acquire = acquire
        else:
            raise NameError('No method acquire')

        if hasattr(lock_inst, 'release'):
            releaseInst = lock_inst.release

            def release():
                logging('release (lock:%s)' % id(lock_inst))
                releaseInst()
                logging('release sucess (lock:%s)' % id(lock_inst))

            lockInst.release = release
        else:
            raise NameError('No method release')

        return lock_inst

    @classmethod
    def check_output(cls, *args, **kwargs):
        ''' Logging version of check_output.
        '''
        try:
            kwargs['stderr'] = subprocess.STDOUT # redirct stderr to stdout
            output = subprocess.check_output(*args, **kwargs)
            return output.rstrip()
        except Exception, e:
            cls.send(LOG_ERROR, str(e))
            raise
