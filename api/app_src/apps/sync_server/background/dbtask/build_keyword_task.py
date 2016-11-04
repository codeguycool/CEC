from framework.background_task import BackgroundTask
from framework.db_client.pg_client import PGClient
from framework.sys_tools import log
from framework.sys_const import LOG_ERROR


class BuildKeywordTask(BackgroundTask):
    """ Build multimedia keyword table task.
    """
    def __init__(self, db, sqlcmd):
        BackgroundTask.__init__(self)
        self.done = False
        self.error = False
        self.error_message = None
        self.db = db
        self.sqlcmd = sqlcmd

    def run(self):
        db_inst = PGClient(db=self.db, timeout=False)
        try:
            db_inst.execute(self.sqlcmd)
            db_inst.commit()
            self.done = True  # task done
        except Exception as e:
            self.error = True
            self.error_message = str(e)
            log.send(LOG_ERROR, str(e), traceback=True)
