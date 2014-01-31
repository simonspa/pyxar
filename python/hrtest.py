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
        self._dut_results = []
        s = (self.dut.roc(0).n_cols,self.dut.roc(0).n_rows)
        for i in range(self.dut.n_rocs):
            self._dut_results.append(numpy.zeros(s))
        self._dut_results = numpy.array(self._dut_results)
        self.data_taking_time = 5
        self.divider = float(self.dut.n_rocs/8)
        if self.divider < 1:
            self.divider = 1
        self._dut_histo = ROOT.TH2F(self.test, self.test, int(self.dut.n_rocs/self.divider*self.dut.roc(0).n_cols), 0., float(self.dut.n_rocs/self.divider*self.dut.roc(0).n_cols), int(self.divider*self.dut.roc(0).n_rows), 0., float(self.divider*self.dut.roc(0).n_rows)) 
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

    def fill_histo(self):
        for roc in self.dut.rocs():
            for pixel in roc.pixels():
                if roc.number < 8:
                    tmpCol = int(8*roc.n_cols-(roc.number*roc.n_cols+pixel.col))
                    tmpRow = int(self.divider*roc.n_rows-pixel.row)
                else:
                    tmpCol = int(roc.number%8*roc.n_cols+pixel.col)+1
                    tmpRow = int(pixel.row+1)
                data = self._dut_results[roc.number][pixel.col][pixel.row]
                if data > 0:
                    self._dut_histo.SetBinContent(tmpCol, tmpRow, data)

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
        self._dut_results += self.tb.get_data()
        self.update_histo()
    
    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self._dut_results[roc.number]}
            self._results.append(plot_dict)
        plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        if self.window:
            self.window.histos.pop()

    def restore(self):
        '''restore saved dac parameters'''
        super(HRTest, self).restore()
        self.tb.daq_disable()
        self.tb.pg_stop()
        self.tb.init_pg(self.config)
        self.tb.init_deser()
