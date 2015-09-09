import test
import time
import ROOT
import numpy
from plotter import Plotter
import random

class PHRatio(test.Test):
    

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = 1
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = 101
        self.tct_wbc = 5
        self.ttk = 16
        self.pulsed_pixels = []
        
        #unmask all pixels
        self.tb.maskAllPixels(False)
        self.tb.init_deser()
        #send reset
        self.tb.pg_setup = [
            ("resetroc",0)]    # pg_resr
        self.tb.set_pg(self.tb.pg_setup)
        self.tb.pg_single(1,2)
        self.tb.pg_stop()

    def __init__(self, tb, config, window):
        super(PHRatio, self).__init__(tb, config)
        self.window = window
        self._dut_histo2 = self._dut_histo.Clone("test")


    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #reset data containers
        self.dut.data = numpy.zeros_like(self.dut.data)
        self.tb.set_dac('Vcal', 200)
        self.tb.set_dac('CtrlReg', 0)
        #test
        for dt in xrange(1,11):
            deltaT = dt*1
            #arm pixel to be tested
            col = 5
            row = 5
            for roc in self.dut.rocs():
                self.tb.testPixel(col, row, True, roc.number)
            self.tb.m_delay(100)
            self.tb.daq_enable()
        
            self.tb.pg_setup = [
                ("resetroc",25),
                ("calibrate",106),
                ("trigger",16),
                ("token",0)]

            self.tb.set_pg(self.tb.pg_setup)
            self.tb.pg_single(1,152)
            self.tb.u_delay(deltaT)
            self.tb.pg_single(1,152)

            self.tb.pg_stop()
            print '%s us' %(deltaT)
            self.readout(config)
            #disarm pixel
            for roc in self.dut.rocs():
                self.tb.testPixel(col, row, False, roc.number)
            self.tb.daq_disable()
            #send a final reset
            self.tb.pg_setup = [
                ("resetroc",0)] 
            self.tb.set_pg(self.tb.pg_setup)
            self.tb.pg_single(1,2)

        self.logger.info('--------------------------')
        self.logger.info('Finished triggering')
        
        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)
        
        
        
    def readout(self, config):       
        n_hits, average_ph, ph_histogram, ph_cal_histogram, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=True)
        self.dut.data += n_hits

    def update_histo(self):
        if not self.window:
            return
        self.fill_histo()
        self.window.update()

    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        #self._histos.append(res)

    def restore(self):
        '''restore saved dac parameters'''
        super(PHRatio, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

