import Test
from helpers import list_to_grid

class Calibrate(Test.Test):

    def prepare(self, config):
        pass

    def run(self, config):
        result = [0] * self.dut.n_pixels
        trim = self.dut.trim_bits
        self.tb.init_roc()
        self.tb.calibrate(10,trim,result)
        self._results = list_to_grid(self.dut.n_rows, self.dut.n_cols, result)
        return
    
    def cleanup(self, config):
        pass
    
