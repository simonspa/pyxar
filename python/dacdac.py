import Test
from helpers import list_to_grid

class DacDac(Test.Test):

    def run(self, config):
        self.logger.info('Running DacDac test')
        dac1 = 12
        dac2 = 26  
        dac_range1 = 256 
        dac_range2 = 256
        n_triggers = 5
        n_results = dac_range1*dac_range2
        result = [0] * n_results
        self.tb.arm_pixel(5,5)
        self.tb.dac_dac(dac1, dac_range1, dac2, dac_range2, n_triggers, result)
        self.tb.disarm_pixel(5,5)
        self.tb.init_roc()
        self._results = list_to_grid(dac_range1, dac_range2, result)
        return 
    
