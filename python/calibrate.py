import test

class Calibrate(test.Test):

    def prepare(self, config):
        self.n_triggers = int(config.get('Calibrate','n_triggers'))

    def run(self, config):
        #self.tb.get_calibrate(self.n_triggers)
        self.tb.get_ping(self.n_triggers)

    def cleanup(self, config):
        pass

    def restore(self, config):
        pass
