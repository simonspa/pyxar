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
        self.cal_delay = int(config.get('Testboard','pg_cal'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.resr_delay = int(config.get('Testboard','pg_resr'))
        self.trg_delay = int(config.get('Testboard','pg_trg'))
        #unmask all pixels
        self.tb.maskAllPixels(False)
        #send reset
        self.pg_setup = [
            ("resetroc",0)]    # pg_resr
        self.tb.set_pg(self.pg_setup)
        self.tb.pg_single()
        # Clear the DAQ buffer:
        self.tb.daq_getbuffer()
        # Prepare for data taking w/ possibly noisy pixels:
        #self.tb.set_delay("triggerdelay",205)
    
    def __init__(self, tb, config, window):
        super(HREfficiency, self).__init__(tb, config)
        self.window = window
        if self.window:
            self.window.histos.extend([self._dut_histo])

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #reset data containers
        self.dut.data = numpy.zeros_like(self.dut.data)
        #loop over all pixels and send 'n_triggers' calibrates
        #self.tb.get_calibrate(self.n_triggers,0x0100)
        for col in range(self.dut.roc(0)._n_cols):
            for row in range(self.dut.roc(0)._n_rows):
                #arm pixel to be tested on all ROCs of DUT
                for roc in self.dut.rocs():
                    self.tb.testPixel(col, row, True, roc.number)
                self.tb.u_delay(100)
                #send reset
                self.pg_setup = [
                    ("resetroc",0)] 
                self.tb.set_pg(self.pg_setup)
                self.tb.pg_single()
                self.tb.u_delay(10)
                #send n_triggers calibrates
                self.pg_setup = [
                    ("calibrate",self.cal_delay + self.tct_wbc), # PG_CAL
                    ("trigger",self.trg_delay),    # PG_TRG
                    ("token",0)]
                for trig in range(self.n_triggers):
                    self.tb.pg_single()
                    self.tb.u_delay(10)
                #disarm pixel
                for roc in self.dut.rocs():
                    self.tb.testPixel(col, row, False, roc.number)
        #send a final reset
        self.pg_setup = [
            ("resetroc",0)] 
        self.tb.set_pg(self.pg_setup)
        self.tb.pg_single()

        self.logger.info('--------------------------')
        self.logger.info('Finished triggering')
        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)

        #get decoded data from testboard
        readout = self.tb.daqGetEventBuffer()
        print 'xxxxxxxxxxxxxxxxx'
        print readout
        print 'xxxxxxxxxxxxxxxxx'

    def update_histo(self):
        if not self.window:
            return
        self.fill_histo()
        self.window.update()

    def cleanup(self, config):
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        self._dut_histo.SetMinimum(0)
        if self.window:
            self.window.histos.pop()
         
    def restore(self):
        '''restore saved dac parameters'''
        super(HREfficiency, self).restore()
        self.tb.set_delays(self.config)
        self.tb.init_pg(self.config)

