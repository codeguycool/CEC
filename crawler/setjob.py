# 3rd
from crontab import CronTab

# proj
from conf.settings import DIR_EDP, DIR_LOG


if __name__ == '__main__':

    cron = CronTab(user=True)

    """ crawler task
    """

    # corntab cmds
    spiders = ['bttt', 'tudou', 'atmovies', 'douban', 'dmm', 'holiday', 'cashbox', 'kubo']
    basecmd = 'python %(dir)s/runspider.py --spider=%(spider)s'
    cmds = {spider: basecmd % {'dir': DIR_EDP, 'spider': spider} for spider in spiders}

    basecmd_daily = 'python %(dir)s/runspider.py --spider=%(spider)s --page=%(page)s'
    cmds['bttt-daily'] = basecmd_daily % {'dir': DIR_EDP, 'spider': 'bttt', 'page': 2}
    cmds['kubo-daily'] = basecmd_daily % {'dir': DIR_EDP, 'spider': 'kubo', 'page': 1}

    # clean job
    for k, v in cmds.iteritems():
        cron.remove_all(comment=k)

    # set job
    job = cron.new(command=cmds['bttt-daily'], comment='bttt-daily')
    job.setall('0 23 * * *')
    job = cron.new(command=cmds['tudou'], comment='tudou')
    job.setall('0 20 * * 5')
    # job = cron.new(command=cmds['atmovies'], comment='atmovies')
    # job.setall('0 20 * * 5')
    job = cron.new(command=cmds['douban'], comment='douban')
    job.setall('0 20 * * 5')
    job = cron.new(command=cmds['dmm'], comment='dmm')
    job.setall('0 20 * * 5')
    job = cron.new(command=cmds['holiday'], comment='holiday')
    job.setall('0 20 * * 2')
    job = cron.new(command=cmds['cashbox'], comment='cashbox')
    job.setall('0 20 * * 5')
    job = cron.new(command=cmds['kubo-daily'], comment='kubo-daily')
    job.setall('0 22 * * *')
    job = cron.new(command=cmds['kubo'], comment='kubo')
    job.setall('0 20 * * 5')

    """ other task
    """

    DIR_CRONTAB_LOG = '%s/crontab' % DIR_LOG
    CMD_SYNCDB = 'python %s/syncdb.py > %s/syncdb.log 2>&1' % (DIR_EDP, DIR_CRONTAB_LOG)
    CMD_UPDATEIMDB = 'python %s/updateimdb.py > %s/updateimdb.log' % (DIR_EDP, DIR_CRONTAB_LOG)

    cron.remove_all(comment='task1')
    job = cron.new(command=CMD_SYNCDB, comment='task1')
    job.setall('30 23 * * *')
    cron.remove_all(comment='task2')
    job = cron.new(command=CMD_UPDATEIMDB, comment='task2')
    job.setall('0 20 * * 5')

    # write to crontab
    cron.write()

    for line in cron.lines:
        print line
