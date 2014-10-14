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
        self.ttk = int(config.get('HREfficiency','ttk'))

        #unmask all pixels
        self.tb.maskAllPixels(False)
        self.tb.init_deser()
        #send reset
        self.tb.pg_setup = [
            ("resetroc",0)]    # pg_resr
        self.tb.set_pg(self.tb.pg_setup)
        self.tb.pg_single(1,2)
        self.tb.pg_stop()
 
#----------------------------------

        #for i in range(self.n_rocs):
        #    self.tb.arm_pixel(i,5,5)
        #self.tb.daq_enable()
        #self.tb.pg_setup = [
        #        ("resetroc",0)]
        #self.tb.set_pg(self.tb.pg_setup)
        #self.tb.pg_single(1,2)
        #self.tb.pg_stop()
 
        #self.tb.pg_setup = [
        #                ("calibrate",106),
        #                ("trigger",ttk),
        #                ("token",0)]
        #self.tb.set_pg(self.tb.pg_setup)

#---------------------------------- 
         
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
        #for col in range(self.dut.roc(0)._n_cols):
        for col in range(1):
            #for row in range(self.dut.roc(0)._n_rows):
            for row in range(1):
                #arm pixel to be tested on all ROCs of DUT
                for roc in self.dut.rocs():
                    self.tb.testPixel(col, row, True, roc.number)
                self.tb.u_delay(100)
                self.tb.daq_enable()
                # Clear the DAQ buffer:
                self.tb.daq_getbuffer()
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
                    self.tb.pg_single(1,142)
                    #print self.tb.daqGetEvent()
                    self.tb.u_delay(10)
                self.tb.pg_stop()
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
        #get decoded data from testboard
        #readout = self.tb.daqGetEvent()
        #print readout
        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)
        print self.dut.data
#-------------------------
#        self.store(config)
#        self.prepare(config)
#        self.start_data = time.time()
#        self.length=0
#        self.logger.info('Start data taking')
        
#        self.tb.pg_loop(self.period)
#        self.tb.m_delay(1000)
#        self.tb.pg_stop()
#    
#        n_hits, average_ph, ph_histogram, ph_cal_histogram, hit_events, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=True)
#        self.dut.data += n_hits
#        self.update_histo()

#        for i in range(self.n_rocs):
#            self.tb.disarm_pixel(i,5,5)
#        self.tb.daq_disable()
#        self.cleanup(config)
#        self.dump()
#        self.restore()
#-------------------------

    def readout(self, config):        
        n_hits, average_ph, ph_histogram, ph_cal_histogram, hit_events, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=True)
        self.dut.data += n_hits
        #for roc in range(self.n_rocs):
        #    self.dut.ph_array[roc].extend(ph_histogram[roc])
        #    self.dut.ph_cal_array[roc].extend(ph_cal_histogram[roc])
        #    self.dut.hit_event_array[roc].extend(hit_events[roc])
        self.update_histo

    def update_histo(self):
        if not self.window:
            return
        self.fill_histo()
        self.window.update()

    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
#        self.fill_histo()
#        for roc in self.dut.rocs():
#            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
#            self._results.append(plot_dict)
#            plot = Plotter(self.config, self)
#        #Create PH histograms for every ROC and whole DUT
#        #for roc in self.dut.rocs():
#        #    ph_adc = numpy.array(self.dut.ph_array[roc.number])
#        #    ph_vcal = numpy.array(self.dut.ph_cal_array[roc.number])
#            #hit_ev = numpy.array(self.dut.hit_event_array[roc.number])
#            #hit_ev_index = []
#            #for i in range(len(hit_ev)):
#            #    hit_ev_index.append([i, hit_ev[i]])
#        #    PH_ADC = Plotter.create_th1(ph_adc,'PH_ADC_ROC_%s' %roc.number, 'ADC units', '# entries', 0, 255)
#        #    PH_VCAL = Plotter.create_th1(ph_vcal,'PH_VCAL_ROC_%s' %roc.number, 'Vcal units', '# entries', 0, 255)
#        #    if len(hit_ev)>0:
#        #        HIT_EV = Plotter.create_tgraph(hit_ev, 'event number modulo 100 for events with hits in pixel 5:5 of ROC %s' %roc.number, 'hit number','event number % 100',0,len(hit_ev))
#        #        self._histos.append(HIT_EV)
#        #    self._histos.append(PH_ADC)
#        #    self._histos.append(PH_VCAL)
#        self._histos.extend(plot.histos)
#        self._histos.extend([self._dut_histo])
#        if self.window:
#            self.window.histos.pop()

#--------------------------
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        if self.window:
            self.window.histos.pop()

#--------------------------

      
    def restore(self):
        '''restore saved dac parameters'''
        super(HREfficiency, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

