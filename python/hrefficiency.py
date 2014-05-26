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
        self.n_rocs = int(config.get('Module','rocs'))
        #send reset
        pg_setup = {
            self.tb.PG_RESR:0}    # PG_RESR
        self.tb.set_pg(pg_setup)
        self.tb.pg_single()
        # Clear the DAQ buffer:
        self.tb.daq_getbuffer()

        # Prepare for data taking w/ possibly noisy pixels:
        self.tb.init_pg(self.config)
        self.tb.set_delay("triggerdelay",205)
    
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
        self.tb.get_calibrate(self.n_triggers,0x0100)
        
        self.logger.info('--------------------------')
        self.logger.info('Finished triggering')
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
        self.tb.set_delays(self.config)
        self.tb.init_pg(self.config)

