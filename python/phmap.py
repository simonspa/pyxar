import test

class PHMap(test.Test):

    def prepare(self, config):
        self.n_triggers = int(config.get('PHMap','n_triggers'))

    def run(self, config):
        self.tb.get_ph(self.n_triggers)

