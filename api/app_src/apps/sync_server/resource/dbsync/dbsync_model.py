# -*-coding: utf-8 -*-

"""Model class
"""

# std module
import re
from threading import Lock

# app module
from dbtask.patchers import create_patcher
from dbtask.keyword_builders import create_keyword_builder
from framework.db_client.pg_client import PGClient
from framework.err import ERR_REQUEST_ARG, RequestError
from framework.response import Response
from framework.sys_tools import g


class DbSyncModel:

    def __init__(self):
        self.mutex = Lock()
        self.bg_task = None

        # todo: if add method, need to wrap method with processing_lock()
        self.rebuild_keyword = self.proccessing_lock(self.rebuild_keyword, 'rebuild_keyword')
        self.patch_data = self.proccessing_lock(self.patch_data, 'patch_data')

    def _check_bg_running(self):
        """ Check background task is running? if error occur or done, then set bg_task to None.
        """
        if self.bg_task:
            taskobj = g().get(self.bg_task)
            # task occur error or done, set bg_task to None
            if taskobj.error or taskobj.done is True:
                self.bg_task = None

    def proccessing_lock(self, func, taskname):
        """ Processing lock decorator.

        Check background task is running? If not, execut func, else return error
        """
        def wrapper(*args, **kwargs):
            try:
                # lock
                self.mutex.acquire()
                # check background task status
                self._check_bg_running()
                # if other task is running, return Response.
                if self.bg_task:
                    return Response(success=False, err_msg='other task is runing.')
                else:
                    self.bg_task = taskname
                    # if no other task run, execute func.
                    return func(*args, **kwargs)
            finally:
                # unlock
                self.mutex.release()
        return wrapper

    def update_latest_movies(self, url, params, request, response):
        """ Update latest movies.

        [Arguments]
            imdbid_list: list
                The imdbid list to update latest table.
        [Return]
            rowcount: int
                The row count of 'movie_latest'.
        """
        imdbid_list = params.get_list('imdbid_list', None)
        # check argument 'imdbid_list'
        if not imdbid_list:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'imdbid_list' is need.",))

        values = ''
        for data in imdbid_list:
            # check imdbid pattern
            reslut = re.match('tt\d{7}', data[0])
            if reslut is None:
                raise RequestError(ERR_REQUEST_ARG, str_data=('imdbid_list(%s) is not imdbid format.' % data[0],))
            values += "('%s', '%s')," % (data[0], data[1])
        values = values[:-1]

        # insert db
        db_inst = PGClient()
        db_inst.execute('truncate table movie_latest')
        db_inst.execute('insert into movie_latest values %s' % values)
        db_inst.commit()
        cur = db_inst.execute('select count(*) from movie_latest')
        rowcount = cur.fetchone()[0]

        return Response(model_data={'rowcount': rowcount})

    def get_last_timestamp(self, url, params, request, response):
        """ get last update timestamp

        create patcher by tablename and get timestamp.

        :param url:
        :param params:
        :param request:
        :param response:
        :return:
        """
        tablename = params.get_string('entity', None)
        # check entity argument
        if not tablename:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'entity' is need.",))

        # get patcher
        patcher = create_patcher(tablename)
        if not patcher:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'entity' is incorrect.",))

        return Response(model_data={'timestamp': patcher.get_timestamp()})

    def get_patch_columns(self, url, params, request, response):
        tablename = params.get_string('tablename', None)
        # check tablename argument
        if not tablename:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'tablename' is need.",))

        # get patcher
        patcher = create_patcher(tablename)
        if not patcher:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'tablename' is incorrect.",))
        # return patch columns
        return Response(model_data={'columns': patcher.get_columns()})

    def patch_data(self, url, params, request, response):
        """ patch data to db

        create patcher by tablename and execute patch.

        :param url:
        :param params:
        :param request:
        :param response:
        :return:
        """
        tablename = params.get_string('tablename', None)
        # check tablename argument
        if not tablename:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'tablename' is need.",))

        # check patchfile argument
        if 'patchfile' not in params:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'patchfile' is need.",))

        # get patcher
        patcher = create_patcher(tablename)
        if not patcher:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'tablename' is incorrect.",))
        # execute patch task
        patcher.patch(params['patchfile'], 'patch_data')
        # return message
        return Response(model_data={'message': "start to patch %s" % patcher.get_tablename()})

    def rebuild_keyword(self, url, params, request, response):
        tablename = params.get_string('tablename', None)
        # check tablename argument
        if not tablename:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'tablename' is need.",))

        # get builder
        builder = create_keyword_builder(tablename)
        if not builder:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'tablename' is incorrect.",))
        # execute rebuild keyword task
        builder.build('rebuild_keyword')
        # return message
        return Response(model_data={'message': 'start to rebuild %s' % builder.get_tablename()})

    def get_task_status(self, url, params, request, response):
        """ Get task status.

        [Arguments]
            task: string
                task name.
                'rebuild_movie_keyword'
                'patch_data'
        [Return]
            task_done: string
                task status.
                True is done, False is not yet.
        """
        task = params.get_string('task', None)
        # check argument 'task'
        if not task:
            raise RequestError(ERR_REQUEST_ARG, str_data=("argument 'task' is need.",))

        taskobj = g().get(task)
        # can't find task
        if not taskobj:
            return Response(success=False, err_msg="can't find task.")
        # some error occur
        if taskobj.error:
            return Response(success=False, err_msg=taskobj.error_message if taskobj.error_message else 'unhandle error')
        # return True: task done; False: not yet
        return Response(model_data={'task_done': taskobj.done})
