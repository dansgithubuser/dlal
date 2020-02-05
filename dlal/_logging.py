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
        logger.addHandler(logging.StreamHandler())
    logger.handlers[0].setLevel(level)

def get_log(name):
    logger = logging.getLogger(name)
    def log(level, message_lambda):
        level = levels[level]
        if level >= logger.level:
            logger.log(level, message_lambda())
    return log
