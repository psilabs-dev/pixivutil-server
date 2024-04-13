import os

class WorkerConfig:

    def __init__(self):
        self.db = ".pixivUtil2/db/db.sqlite"
        self.subscription_time_seconds = int(os.getenv('WORKER_SUBSCRIPTION_TIME_SECONDS', '60'))

config = WorkerConfig()
