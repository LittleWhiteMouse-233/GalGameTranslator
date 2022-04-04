import logging
import logging.handlers
import os.path
import sys
import tkinter.messagebox as tmsg

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
        return MyLogger(mylogger)


class MyLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log(self, level: int, msg: str, *args):
        self.logger.log(level, msg, *args)

    def debug(self, msg: str, *args):
        self.logger.debug(msg, *args)

    def info(self, msg: str, *args):
        self.logger.info(msg, *args)

    def warning(self, msg: str, *args):
        self.logger.warning(msg, *args)
        tmsg.showwarning("警告", msg % args)

    def error(self, msg, *args):
        self.logger.error(msg, *args)
        tmsg.showerror("错误", msg % args)

    def critical(self, msg: str, *args):
        self.logger.critical(msg, *args)
        tmsg.showerror("崩溃", msg % args)
