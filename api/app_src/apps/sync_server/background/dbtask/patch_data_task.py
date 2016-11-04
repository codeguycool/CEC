# std
import hashlib
import os
import zipfile

# project
from app_var import DIR_TEMP_PATH
from framework.background_task import BackgroundTask
from framework.db_client.pg_client import PGClient
from framework.sys_tools import log
from framework.sys_const import LOG_ERROR


class PatchDataTask(BackgroundTask):
    """ Patch multimedia table task

    """

    def __init__(self, fileobj, patcher):
        BackgroundTask.__init__(self)
        self.done = False
        self.error = False
        self.error_message = None
        self.fileobj = fileobj
        self.patcher = patcher

    def run(self):
        patch_data = None

        try:
            patch_data = PatchData(DIR_TEMP_PATH, self.fileobj)

            # patch db
            db_inst = PGClient(self.patcher.db, timeout=False)
            with open(patch_data.get_filepath(), mode='r') as f:
                db_inst.execute('begin;')

                # create temp table
                db_inst.execute(self.patcher.temp_table_sqlcmd)

                # file obj column order must match temp table column order
                db_inst.copy_from(f, self.patcher.temp_table_name)

                db_inst.execute(self.patcher.sqlcmd)
                db_inst.execute('commit;')

            # task done
            self.done = True
        except Exception as e:
            self.error = True
            self.error_message = e.message if e.message is not None else vars(e)
            log.send(LOG_ERROR, self.error_message, traceback=True)
        finally:
            if patch_data is not None:
                patch_data.remove()


class PatchData(object):
    """ Process patch file

    unzip patch file

    """

    dirpath = None
    filename = None
    md5sum = None

    def __init__(self, dirpath, fileobj):
        self.dirpath = dirpath
        self.filename = fileobj.filename

        # check directory exists
        if not os.path.exists(dirpath):
            raise Exception("directory is not exist.")

        # write file & calc md5sum
        md5 = hashlib.md5()
        with open(self.get_filepath(), mode='wb') as fp:
            while True:
                data = fileobj.file.read(8192)
                if data:
                    fp.write(data)
                    md5.update(data)
                else:
                    break

        if md5.hexdigest().lower() != self.filename:
            raise Exception('md5 value is incorrect')

        self.unzip()

    def unzip(self):
        csv_filename = None
        with zipfile.ZipFile(self.get_filepath()) as datazip:
            if len(datazip.filelist) != 1:
                raise Exception('file number greater than one.')
            datazip.extract(datazip.filelist[0], self.dirpath)
            csv_filename = datazip.filelist[0].filename

        self.remove()
        self.filename = csv_filename

    def get_filepath(self):
        return '%s/%s' % (self.dirpath, self.filename)

    def remove(self):
        if os.path.exists(self.get_filepath()):
            os.remove(self.get_filepath())
