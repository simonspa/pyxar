import Test
from helpers import list_to_grid

class DacDac(Test.Test):

    def run(self, config):
        self.logger.info('Running DacDac test')
        dac1 = int(config.get('DacDac','dac1'))
        dac2 = int(config.get('DacDac','dac2'))
        n_triggers = int(config.get('DacDac','n_triggers'))
        for roc in self.dut.rocs():
            dac_range1 = roc.dac(dac1).range
            dac_range2 = roc.dac(dac2).range
            n_results = dac_range1*dac_range2
            for pixel in roc.active_pixels():
                result = [0] * n_results
                self.tb.arm(pixel)
                self.tb.dac_dac(dac1, dac_range1, dac2, dac_range2, n_triggers, result)
                self.tb.disarm(pixel)
                self._results = list_to_grid(dac_range1, dac_range2, result)
        return 
    
