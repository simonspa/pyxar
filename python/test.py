import logging

class Test(object):

    def __init__(self, tb, dut, config = None):
        self.tb = tb
        self.dut = dut
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._results = None

    def prepare(self, config):
        pass

    def run(self, config):
        pass
    
    def cleanup(self, config):
        pass

    @property
    def results(self):
        return self._results
