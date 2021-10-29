# Custom logger
import logging as log


def __set_logger(self, quiet: bool, debug: bool):
    level = log.INFO
    if quiet:
        level = log.WARN
    if debug:
        level = log.DEBUG

    # use stream handler
    handler = log.StreamHandler()
    formatter = log.Formatter('%(name)s %(levelname)s: %(message)s')

    # apply settings
    handler.setLevel(level)
    handler.setFormatter(formatter)

    self.setLevel(level)
    self.addHandler(handler)
    self.propagate = False


def get_logger(name: str):
    log.Logger.set_logger = __set_logger
    return log.getLogger(name)
