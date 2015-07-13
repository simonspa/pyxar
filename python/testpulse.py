import test
import time
import ROOT
import numpy
from plotter import Plotter
import random

class TestPulse(test.Test):
    ''' send n calibrates to a specific pixels'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = 100
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = int(config.get('Testboard','pg_cal'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.ttk = 16
        self.pulsed_pixels = []
        self.shape = (52,80)

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
        super(TestPulse, self).__init__(tb, config)
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

        #loop over all pixels and send 'n_triggers' calibrates
        for col in range(1):
            #for row in range(self.dut.roc(0)._n_rows):
            for row in range(1):
                #pixel under test
                col = col*2+int(random.random()+.5)
                #col =4
                row = int(random.random()*80)
                self.pulsed_pixels.append([col,row])
                #arm pixel to be tested on all ROCs of DUT
                for roc in self.dut.rocs():
                    self.tb.testPixel(col, row, True, roc.number)
                self.tb.u_delay(100)
                self.tb.daq_enable()
                # Clear the DAQ buffer:
                #self.tb.daq_getbuffer()
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
        
        self.dut.ph_array = self.dut.data
        self.dut.ph_cal_array = numpy.zeros_like(self.dut.data) 
        
        for pix in range(len(self.pulsed_pixels)):
            pcol = self.pulsed_pixels[pix][0]
            prow = self.pulsed_pixels[pix][1]
            #set entry in pulsed pixel to zero (by definition no fake hits in pulsed pixels)
            self.dut.ph_array[0][pcol][prow]=0.
            
            self.dut.ph_cal_array[0][pcol][prow] = - (self.dut.data[0][pcol][prow] - self.n_triggers)


        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)
        
        
        
    def readout(self, config):       
        n_hits, average_ph, ph_histogram, ph_cal_histogram, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=True)
        self.dut.data += n_hits
        #for roc in range(self.n_rocs):
        #    self.dut.ph_array[roc].extend(ph_histogram[roc])
        #    self.dut.ph_cal_array[roc].extend(ph_cal_histogram[roc])
        #    self.dut.hit_event_array[roc].extend(hit_events[roc])
        #self.update_histo

    def update_histo(self):
        if not self.window:
            return
        self.fill_histo()
        self.window.update()

    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        
        
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        #self._histos.extend([self._dut_histo2])

        all_hits = Plotter.create_th2(self.dut.data[0],52,80,"all hits", "col", "row")
        self._histos.append(all_hits)
        missing_hits = Plotter.create_th2(self.dut.ph_cal_array[0],52,80,"missing hits", "col", "row")
        self._histos.append(missing_hits)
        fake_hits = Plotter.create_th2(self.dut.ph_array[0],52,80,"fake hits", "col", "row")
        self._histos.append(fake_hits)

        #calculate rates
        n_fakes = numpy.sum(self.dut.ph_array)
        n_miss = numpy.sum(self.dut.ph_cal_array)

        fake_rate = n_fakes / float((len(self.pulsed_pixels)*self.n_triggers))
        miss_rate = n_miss / (len(self.pulsed_pixels)*self.n_triggers)

        self.logger.info('----------------------------------------------------------')
        self.logger.info('number of fake hits:              %s ' %n_fakes)
        self.logger.info('number of missing test pulses:    %s ' %n_miss)
        self.logger.info('fake hit rate:                    %s fake hits per test pulse       ' %round(fake_rate,5))
        self.logger.info('test pulse miss rate:             %s per cent of test pulses missing' %round(miss_rate*100,5))
        self.logger.info('----------------------------------------------------------')

    def restore(self):
        '''restore saved dac parameters'''
        super(TestPulse, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

