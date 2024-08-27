from datetime import datetime
import logging

levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'verbose': 5,
}

logging.addLevelName(levels['verbose'], 'VERBOSE')

class Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created).isoformat(' ')

formatter = Formatter('%(asctime)s %(message)s')

def get_logger_names():
    return [
        i
        for i in logging.root.manager.loggerDict
        if i.startswith('dlal')
    ]

def set_logger_level(name, level):
    level = levels[level]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.handlers[0].setLevel(level)

def get_log(name):
    logger = logging.getLogger(name)
    def log(level, message):
        level = levels[level]
        if level >= logger.level:
            if callable(message): message = message()
            logger.log(level, message)
    return log
