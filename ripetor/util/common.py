import logging


def get_default_format():
    return '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # old formatter: return '%(asctime)s %(levelname)-8s %(message)s'


def get_console_logger(name):
    logger = logging.getLogger(name)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    # create formatter
    log_format = get_default_format()
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    return logger


def get_file_logger(name, log_file):
    log_format = get_default_format()

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        filename=log_file,
        filemode="w"
    )

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(log_format))

    logger = logging.getLogger(name)
    logger.addHandler(console)
    return logger


def set_global_file_logger(log_file, debug=False):
    log_format = get_default_format()

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        filename=log_file,
        filemode="w"
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format))

    if debug:
        console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)
