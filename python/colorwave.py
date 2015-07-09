import test
import time
import ROOT
import numpy
from plotter import Plotter
import random

class ColOrWave(test.Test):
    ''' alternative test to measure the speed of the ColOr wave 
    along the double column. Results should be the same as with the HldDelay test.
    Here one pixel in double column A is always enabled. In another double column B
    it is iterated over all pixels of the dcol. In each iteration first only pixel A
    and then pixel A and B are pulsed. The difference of the PH of pixel A in both 
    measurments is histogrammed as a function of the position of the pixel in dcol B.''' 

    def __init__(self, tb, config, window):
        super(ColOrWave, self).__init__(tb, config)
        self.window = window
        self.start_data = 0
        self.shape = (26,160)
        self.result = numpy.zeros(self.shape)
        self.res_histo = ROOT.TH2F(self.test, self.test, 26, 0., 26, 160, 0., 160)

        self.n_rocs = int(config.get('Module','rocs'))
        if self.window:
            self.window.histos.extend([self.res_histo])

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = 10
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = int(config.get('Testboard','pg_cal'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.ttk = 16
        self.tb.maskAllPixels(False)
        self.tb.init_deser()
        #send reset
        self.tb.pg_setup = [
            ("resetroc",0)]    # pg_resr
        self.tb.set_pg(self.tb.pg_setup)
        self.tb.pg_single(1,2)
        self.tb.pg_stop()

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #reset data containers
        self.dut.data = numpy.zeros_like(self.dut.data)
        #pick a fixed pixel in dcol A
        self.colA = 14
        self.rowA = 30
        #start
        for roc in self.dut.rocs():
            #loop over all columns
            for icol in range(26):
                #loop over all pixels of the dcol B
                for irow in range(160):
                    if irow < 80:
                        self.rowB = irow
                        self.colB = icol*2
                    else:
                        self.rowB = -irow+159
                        self.colB = icol*2+1
                    print 'testing pixels %i:%i and %i:%i' %(self.colA, self.rowA, self.colB, self.rowB) 
                    #abort if more than one ROC
                    if self.n_rocs>1:
                        self.logger.warning('Test not compatible with DUT with more than 1 ROC - aborting')
                        break
                    #first measure pixel A only
                    self.tb.testPixel(self.colA, self.rowA, True, 0)
                    self.tb.daq_enable()
                    #send reset
                    self.tb.pg_setup = [
                        ("resetroc",0)]    # pg_resr
                    self.tb.set_pg(self.tb.pg_setup)
                    self.tb.pg_single(1,2)
                    self.tb.pg_stop()
                    self.tb.u_delay(10)
                    #set up pg for sending Vcals
                    self.tb.pg_setup = [
                        ("calibrate",self.cal_delay + self.tct_wbc), 
                        ("trigger",self.ttk),    
                        ("token",0)]
                    self.tb.set_pg(self.tb.pg_setup)
                    #send n_triggers Vcal pulses to pixel under test
                    for trig in range(self.n_triggers):
                        self.tb.pg_single(1,127)
                        #print self.tb.daqGetEvent()
                        self.tb.u_delay(10)
                    self.tb.pg_stop()
                    self.readout(config)
                    ph_without = self.dut.data[0][self.colA][self.rowA]
                    self.dut.data = numpy.zeros_like(self.dut.data)
                    self.tb.daq_disable() 
                    #now also enable iterative pixel
                    self.tb.testPixel(self.colB, self.rowB, True, 0)
                    self.tb.daq_enable()
                    self.tb.pg_setup = [
                        ("resetroc",0)]    # pg_resr
                    self.tb.set_pg(self.tb.pg_setup)
                    self.tb.pg_single(1,2)
                    self.tb.pg_stop()
                    self.tb.u_delay(10)
                    #set up pg for sending Vcals
                    self.tb.pg_setup = [
                        ("calibrate",self.cal_delay + self.tct_wbc), 
                        ("trigger",self.ttk),    
                        ("token",0)]
                    self.tb.set_pg(self.tb.pg_setup)
 
                    #send n_triggers Vcal pulses to pixel under test
                    for trig in range(self.n_triggers):
                        self.tb.pg_single(1,127)
                        #print self.tb.daqGetEvent()
                        self.tb.u_delay(10)
                    self.tb.pg_stop()
                    self.readout(config)
                    ph_with = self.dut.data[0][self.colA][self.rowA]
                    self.dut.data = numpy.zeros_like(self.dut.data)
                    self.tb.daq_disable() 

                    self.tb.testAllPixels(False)
                    deltaPH = ph_with - ph_without
                    print '-----'
                    print deltaPH
                    print '-----'
                    self.result[icol][irow] = deltaPH
                    self.update_histo()
                    self.res_histo.SetBinContent(icol+1,irow+1,self.result[icol][irow])
                    ph_without = 0
                    ph_with = 0
                    deltaPH = 0

        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)
    
    def update_histo(self):
        if not self.window:
            return
        self.window.update()
        
    def readout(self, config):       
        n_hits, average_ph, ph_histogram, ph_cal_histogram, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=False)
        self.dut.data += average_ph


    def cleanup(self, config):
        plot = Plotter(self.config, self)
        res = Plotter.create_th2(self.result,26, 160, "delta PH pix %i:%i" %(self.colA, self.rowA), "dcol", "pixel")
        self._histos.append(res)
        self._histos.extend(plot.histos)
        self._histos.extend([self.res_histo])
        if self.window:
            self.window.histos.pop()


 
    def restore(self):
        '''restore saved dac parameters'''
        super(ColOrWave, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

