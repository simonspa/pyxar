import Test
from helpers import list_to_grid

class Threshold(Test.Test):

    def run(self, config): 
        self.logger.info('Running %s test' %__name__)
        start = 100
        step = 1
        n_triggers = 50
        thr_level = int(n_triggers/2.)
        cals = True
        xtalk = False
        dac_reg = 25
        for roc in self.dut.rocs():
            self.logger.info('Start: %s, step: %s, thr_level: %s, n_triggers: %s, dac_reg: %s, xtalk: %s, cals: %s' %(start, step, thr_level, n_triggers, dac_reg, xtalk, cals))
            self.tb.init_roc()
            result = [0] * roc.n_pixels
            trim = [15] * roc.n_pixels
            self.tb.chip_threshold(start, step, thr_level, n_triggers, dac_reg, xtalk, cals, trim, result)
            self._results = list_to_grid(roc.n_rows, roc.n_cols, result)
            print self._results
        return
    
