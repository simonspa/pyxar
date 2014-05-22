import test
import time
import ROOT
import numpy
from plotter import Plotter

class HREfficiency(test.Test):
    ''' send n calibrates to each pixels and get readout with address while DUT is exposed to high x-radiation rate'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = int(config.get('HREfficiency','n_triggers'))
        self.ttk = int(config.get('HREfficiency','ttk'))
        self.n_rocs = int(config.get('Module','rocs'))
        #enable all columns
        for roc in self.dut.rocs():
            self.tb.select_roc(roc)
            for col in range(roc.n_cols):
                self.tb.enable_column(col)
        #set up the perifery
        self.tb.pg_stop()
        self.tb.init_deser()
        self.tb.daq_enable()
        #send reset
        self.tb.pg_setcmd(0, self.tb.PG_RESR)
        self.tb.pg_single()
    
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
        self.tb.init_pg(self.tb.config)        
        for roc in self.dut.rocs():
            self.tb.select_roc(roc)
            self.logger.info('Sending calibrates to %s' %roc)
            for col in range(roc.n_cols):
                for row in range(roc.n_rows):
                    #Arm this pixel
                    self.tb.arm_pixel(col, row)
                    self.tb.u_delay(5)
                    #send 'n_triggers' calibrates and consecutive triggers
                    for trig in range(self.n_triggers):
                        self.tb.pg_single()
                        self.tb.u_delay(4)
                    #disarm the pixel
                    self.tb.disarm_pixel(col,row)
            self.take_data(config)
        

        self.logger.info('--------------------------')
        self.logger.info('Finished triggering')
        self.tb.daq_disable()
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
        n_hits, average_ph, ph_histogram, ph_cal_histogram, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=False)
        self.dut.data += n_hits
        self.update_histo()

    def cleanup(self, config):
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        if self.window:
            self.window.histos.pop()
         
    def restore(self):
        '''restore saved dac parameters'''
        super(HREfficiency, self).restore()
        self.tb.daq_disable()
        self.tb.pg_stop()
        self.tb.init_pg(self.config)
        self.tb.init_deser()

