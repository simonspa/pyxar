import test

class Calibrate(test.Test):

    def prepare(self, config):
        self.n_triggers = int(config.get('Calibrate','n_triggers'))

    def run(self, config):
        self.tb.get_calibrate(self.n_triggers)
