import test
from plotter import Plotter

class PHScan(test.Test):
    ''' scan through a DAC vs. resulting pulseheight for n injected calibrates '''

    def prepare(self, config):
        self.dac = config.get('PHScan','dac')
        self.n_triggers = int(config.get('PHScan','n_triggers'))
        self.y_title = self.dac
        self.x_title = 'Pulse Height'

    def run(self, config):
        self.logger.info('Running PH Scan')
        self.tb.get_ph_dac(self.n_triggers, self.dac)

    def cleanup(self, config):
        for roc in self.dut.rocs():
            for pixel in roc.active_pixels():
                plot = Plotter.create_tgraph(pixel.data, 'ROC_%s_Pix_(%s,%s)' %(roc.number,pixel.col,pixel.row), self.dac, 'Pulseheight',0, roc.dac(self.dac).range)
                self._histos.append(plot)
