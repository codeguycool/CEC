""" Shared tools.
"""
from api.const import USER_ACTION_VIEW, USER_ACTION_DOWNLOAD, USER_ACTION_PLAY


# Counter of User Actions.
def UA2field(action_type):
    return {
        USER_ACTION_VIEW: 'vcount',
        USER_ACTION_DOWNLOAD: 'dcount',
        USER_ACTION_PLAY: 'pcount'
    }[action_type]
