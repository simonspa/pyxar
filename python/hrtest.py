import time
import numpy
import ROOT
import test
from plotter import Plotter

class HRTest(test.Test):

    def __init__(self, tb, config, window):
        super(HRTest, self).__init__(tb, config)
        self.window = window
        self.start_data = 0
        self.dut.data = []
        self.data_taking_time = 5
        if self.window:
            self.window.histos.extend([self._dut_histo])

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        while time.time() - self.start_data < self.data_taking_time:
            self.take_data(config)
        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time 
        self.logger.info('Test finished after %.1f seconds' %delta_t)

    def update_histo(self):
        if not self.window:
            return
        self.fill_histo()
        self.window.update()

    def take_data(self, config): 
        '''Main test on DUT and TB.'''
        time_left = self.data_taking_time - (time.time() - self.start_data)
        #TODO implement progress bar
        if round(time_left%5.,1) < 0.1 or round(time_left%5.,1) > 4.9:
            self.logger.info('Test is running for another %.0f seconds' %(time_left) )
        self.dut.data += self.tb.get_data()
        self.update_histo()
    
    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
        plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        hits = plot->GetEntries()
        self.logger.info('Number of hits %i' %hits) )
        if self.window:
            self.window.histos.pop()

    def restore(self):
        '''restore saved dac parameters'''
        super(HRTest, self).restore()
        self.tb.daq_disable()
        self.tb.pg_stop()
        self.tb.init_pg(self.config)
        self.tb.init_deser()
