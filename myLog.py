import logging
import logging.handlers
import os.path
import sys

LOG_PATH = 'log'


class LoggerCreator:
    @staticmethod
    def get_default_logger(*, name: str = 'mylogger'):
        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)
        mylogger = logging.getLogger(name)
        mylogger.setLevel(logging.DEBUG)

        file_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(LOG_PATH, name + '.log'), when='midnight',
                                                                 interval=1,
                                                                 backupCount=10)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(thread)s - %(message)s"))

        mylogger.addHandler(file_handler)
        mylogger.addHandler(console_handler)
        return mylogger
