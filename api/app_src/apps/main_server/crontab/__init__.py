"""Crontab
"""

# 3rd party library
import timer2

# app module
import scavenger


# Task format: {'function': func, 'seconds': seconds}
# Apply task after n secs
applyAfter = [
]

# Apply task every n secs
applyInterval = [
    {'function': scavenger.clear_addons_cache, 'seconds': 60*60*24}
]


# Task start
for job in applyAfter:
    timer2.Timer().apply_after(**{
        'msecs': job['seconds'] * 1000,
        'fun': job['function']
    })

for job in applyInterval:
    timer2.Timer().apply_interval(**{
        'msecs': job['seconds'] * 1000,
        'fun': job['function']
    })
