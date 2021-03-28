# The CLI utility library
import logging as log

def set_level(self, level):
    # use stream handler
    handler = log.StreamHandler()
    formatter = log.Formatter('%(name)s %(levelname)s: %(message)s')

    # apply settings
    handler.setLevel(level)
    handler.setFormatter(formatter)

    self.setLevel(level)
    self.addHandler(handler)
    self.propagate = False

