import Test
from helpers import list_to_grid

class DacDac(Test.Test):

    def run(self, config):
        self.logger.info('Running DacDac test')
        dac1 = int(config.get('DacDac','dac1'))
        dac2 = int(config.get('DacDac','dac2'))
        n_triggers = int(config.get('DacDac','n_triggers'))
        self._results = self.tb.get_dac_dac(n_triggers, dac1, dac2)
        return 
    
