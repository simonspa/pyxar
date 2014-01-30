import logging
import time
import os
import numpy
import ROOT
from plotter import Plotter

class HRTest(object):

    def __init__(self, tb, config, window):
        self.tb = tb
        self.dut = tb.dut
        self.config = config
        self.window = window
        self.name = self.__class__.__name__
        self.directory = '%s/%s' %(self.config.get('General','work_dir'),self.name)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.logger = logging.getLogger(self.name)
        test_logger = logging.FileHandler('%s/test.log' %self.directory)
        self.logger.addHandler(test_logger)
        self.test = str(self.__class__.__name__)
        self.x_title = 'Column'
        self.y_title = 'Row'
        self.start_data = 0
        self._results = []
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
        self._histos = []

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

    def store(self, config):
        '''save dac parameters before test'''
        self.dut.store_dacs()

    def prepare(self, config):
        '''Fetch everything from config.'''
        pass

    def fill_histo(self):
        for roc in self.dut.rocs():
            for pixel in roc.pixels():
                tmpCol = int(self.dut.n_rocs*roc.n_cols-(roc.number*roc.n_cols+pixel.col))
                tmpRow = int(self.divider*roc.n_rows-pixel.row)
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
            self.window.histos.extend(self._histos)
            self.window.update()

    def restore(self):
        '''restore saved dac parameters'''
        self.tb.daq_disable()
        self.tb.pg_stop()
        self.tb.init_pg(self.config)
        self.tb.init_deser()
        for roc in self.dut.rocs():
            for dac in roc.dacs():
                if dac.changed:
                    self.tb.set_dac_roc(roc,dac.number,dac.stored_value)
                    self.logger.info('restore %s'%dac)
    
    def dump(self):
        '''Dump results in folder'''
        #Write config
        config_file = open('%s/config' %(self.directory), 'w')
        self.config.write(config_file)
        config_file.close()
        #Write ROC settings
        for roc in self.dut.rocs():
            roc.save('', self.directory)
        #Write HISTOS
        #TODO does RECREATE make sense?
        a_file = ROOT.TFile('%s/result.root' %(self.directory), 'RECREATE' )
        for histo in self._histos:
            histo.Write()
        a_file.Close()

    @property
    def results(self):
        return self._results
    
    @property
    def histos(self):
        return self._histos
