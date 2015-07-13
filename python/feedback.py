import test
import time
import ROOT
import numpy
from plotter import Plotter
import random

class Feedback(test.Test):
    '''Test shaper feedback working range by sending a leading 
    test pulse and a following one delta t later. The following 
    pulse is triggered on and it is tested for which delta t and 
    VwllSh settings the leading pulse disables the shaper such 
    that the triggered pulse is not registered'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = 1
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = 101
        self.tct_wbc = 5
        self.ttk = 16
        self.pulsed_pixels = []
        
        self.fbinning = 25
        self.tbinning = 20
        self.feedback_max = 250
        self.deltaT_max = 200
        
        self.shape = ( int(self.feedback_max / self.fbinning), int(self.deltaT_max / self.tbinning) )
        self.result = numpy.zeros(self.shape)
        
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
        super(Feedback, self).__init__(tb, config)
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
        self.tb.set_dac('Vcal', 255)
        self.tb.set_dac('CtrlReg', 4)
        #loop over shaper feedback setting
        for fbin in range(int(self.feedback_max / self.fbinning)):
            self.feedback = fbin * self.fbinning
            self.tb.set_dac('VwllSh', self.feedback)
            #loop over all delta t settings (in number of clk cycles)
            for tbin in range(int(self.deltaT_max / self.tbinning)):
                self.deltaT = tbin * self.tbinning
                print self.deltaT
                #protection not to stop the pg
                if self.deltaT == 0:
                    self.deltaT =1
                #arm pixel to be tested
                col = 5
                row = 5
                for roc in self.dut.rocs():
                    self.tb.testPixel(col, row, True, roc.number)
                self.tb.u_delay(100)
                self.tb.daq_enable()
                # Clear the DAQ buffer:
                #self.tb.daq_getbuffer()
                #send reset
                #self.tb.pg_setup = [
                #    ("resetroc",0)]    # pg_resr
                #self.tb.set_pg(self.tb.pg_setup)
                #self.tb.pg_single(1,2)
                #self.tb.pg_stop()
                #self.tb.u_delay(10)
                #set up pg for sending Vcals
              
                #reproduced DacDac problem
                self.tb.pg_setup = [
                    ("resetroc",25),
                    ("calibrate",self.cal_delay + self.tct_wbc),
                    ("trigger",self.ttk),
                    #("token",self.deltaT),
                    ("resetroc",26),
                    ("calibrate",self.cal_delay + self.tct_wbc), 
                    ("trigger",self.ttk),    
                    ("token",0)]
               

                
                
                
                self.tb.set_pg(self.tb.pg_setup)
                self.tb.pg_single(1,500)
                self.tb.pg_stop()
                self.readout(config)
                #disarm pixel
                for roc in self.dut.rocs():
                    self.tb.testPixel(col, row, False, roc.number)
                self.tb.daq_disable()
                #attach result to the result array
                self.result[fbin,tbin] = self.dut.data[0][col,row]
                self.dut.data = numpy.zeros_like(self.dut.data)
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
        res = Plotter.create_th2_binned(self.result,self.feedback_max, int(self.feedback_max / self.fbinning), self.deltaT_max, int(self.deltaT_max / self.tbinning),"shaper feedback working range", "VwllSh", "delta T (clk cycles)")
        self._histos.append(res)

    def restore(self):
        '''restore saved dac parameters'''
        super(Feedback, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

