import test
from plotter import Plotter

class DacScan(test.Test):
    ''' scan through a DAC vs. resulting efficiency for n injected calibrates '''

    def prepare(self, config):
        self.dac = config.get('DacScan','dac')
        self.n_triggers = int(config.get('DacScan','n_triggers'))
        self.y_title = self.dac
        self.x_title = 'Hits'

    def run(self, config):
        self.logger.info('Running Dac Scan')
        self.tb.get_dac_scan(self.n_triggers, self.dac)

    def cleanup(self, config):
        for roc in self.dut.rocs():
            for pixel in roc.active_pixels():
                plot = Plotter.create_tgraph(pixel.data, 'ROC_%s_Pix_(%s,%s)' %(roc.number,pixel.col,pixel.row), self.dac, 'Hits',0, roc.dac(self.dac).range)
                self._histos.append(plot)
