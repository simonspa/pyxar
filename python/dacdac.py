import test
from plotter import Plotter

class DacDac(test.Test):

    def prepare(self, config):
        self.dac1 = config.get('DacDac','dac1')
        self.dac2 = config.get('DacDac','dac2')
        self.n_triggers = int(config.get('DacDac','n_triggers'))
        self.y_title = self.dac1
        self.x_title = self.dac2

    def run(self, config):
        self.tb.m_delay(7000)
        self.logger.info('Running DacDac test')
        self.tb.get_dac_dac(self.n_triggers, self.dac1, self.dac2)

    def cleanup(self, config):
        for roc in self.dut.rocs():
            for pixel in roc.active_pixels():
                plot_dict = {'title':'ROC_%s_Pix_(%s,%s)' %(roc.number,pixel.col,pixel.row),
                            'x_title': self.x_title, 'y_title': self.y_title, 'data': pixel.data}
                self._results.append(plot_dict)
        plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
