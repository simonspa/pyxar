import Test
from helpers import list_to_grid

class Calibrate(Test.Test):

    def run(self, config):
        for roc in self.dut.rocs():
            result = [0] * roc.n_pixels
            trim = [15] * roc.n_pixels
            self.tb.init_roc()
            self.tb.calibrate(10,trim,result)
            self._results = list_to_grid(roc.n_rows, roc.n_cols, result)
        return
    
