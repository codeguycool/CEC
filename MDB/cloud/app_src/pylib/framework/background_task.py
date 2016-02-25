import threading


class BackgroundTask(threading.Thread):
    '''Super class for background task
    '''
    def __init__(self):
        super(BackgroundTask, self).__init__()
        self.daemon = True

    def run(self):
        pass
