import test
import time
import ROOT
import numpy
from plotter import Plotter

class HREfficiency(test.Test):
    ''' send n calibrates to each pixels and get readout with address while DUT is exposed to x-radiation'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = int(config.get('HREfficiency','n_triggers'))
        self.n_rocs = int(config.get('Module','rocs'))
        #containers to hold vcal and xray hits
        self.vcals = []
        self.xrays = []
        self.shape = (52,80)

    def __init__(self, tb, config, window):
        super(HREfficiency, self).__init__(tb, config)
        self.window = window
        self._dut_histo2 = self._dut_histo.Clone("test")
        #if self.window:
        #    self.window.histos.extend([self._dut_histo])
        #    self.window.histos.extend([self._dut_histo2])
            

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #enable all pixels
        self.tb.testAllPixels(True)
        #flag 0x0180 is FLAG_FORCE_UNMASKED to unmask pixels not under test
        #and FLAG_CHECK_ORDER to separate vcals from xray hits
        data = self.tb.getEfficiencyMap(0x0180, self.n_triggers) 
        for i in range(self.dut.n_rocs):
            self.vcals.append(numpy.zeros(self.shape))
            self.xrays.append(numpy.zeros(self.shape))
        for px in data:
            #number of hits positive means vcal hits
            if px.value >= 0:
                self.vcals[px.roc][px.column][px.row] += px.value
            else:
                self.xrays[px.roc][px.column][px.row] += -1*px.value
        print self.vcals
        print self.xrays
        self.dut.data = self.vcals
        #abuse dut.ph_array container for xray hits
        self.dut.ph_array = self.xrays

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

    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s_Vcal_hits' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            #plot = Plotter(self.config, self)
            plot_dict = {'title':self.test+'_ROC_%s_Xray_hits' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.ph_array[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
            #additional histograms


        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        self._histos.extend([self._dut_histo2])
        #if self.window:
        #    self.window.histos.pop()

    def restore(self):
        '''restore saved dac parameters'''
        super(HREfficiency, self).restore()

