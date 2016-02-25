# std lib
import os
import sys

# 3rd lib
from crontab import CronTab

# add porject path to sys.path
CUR_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(CUR_PATH))

# proj lib
from CEC.settings import DIR_PROJ, DIR_LOG

# corntab cmds
spiders = ['bttt', 'tudou', 'chinayes', 'dmm']
basecmd = 'python %s/spiders/{spider}_spider.py > %s/{spider}.log 2>&1' % (DIR_PROJ, DIR_LOG)
basecmd = basecmd.replace('{spider}', '%(spider)s')
cmds = {spider: basecmd % {'spider': spider} for spider in spiders}

# set crontab
cron = CronTab(user=True)

jobs = cron.find_command(cmds['bttt'])
if jobs:
    pass