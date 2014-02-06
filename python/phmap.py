import test

class PHMap(test.Test):
    ''' inject n calibrates to pixels and get average pulseheight, address decoded '''

    def prepare(self, config):
        self.n_triggers = int(config.get('PHMap','n_triggers'))

    def run(self, config):
        self.tb.get_ph(self.n_triggers)

