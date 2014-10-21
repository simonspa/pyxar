import test
import time
import ROOT
import numpy
from plotter import Plotter

class HREfficiencyScan(test.Test):
    ''' scan over DAC and measure efficiency while DUT is exposed to x-radiation'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = int(config.get('HREfficiencyScan','n_triggers'))
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = int(config.get('Testboard','pg_cal'))
        self.resr_delay = int(config.get('Testboard','pg_resr'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.ttk = int(config.get('HREfficiencyScan','ttk'))
        self.scan_dac = config.get('HREfficiencyScan','scan_dac')
        self.step = int(config.get('HREfficiencyScan','step'))
        self.dac_min = int(config.get('HREfficiencyScan','dac_min'))
        self.dac_max = int(config.get('HREfficiencyScan','dac_max'))
        self.sensor_area = self.n_rocs * 52 * 80 * 0.01 * 0.015 #in cm^2
        self.triggers = self.n_rocs * 4160 * self.n_triggers
        self.shape = (52,80)
        self.eff = []
        self.rate = []

    def __init__(self, tb, config, window):
        super(HREfficiencyScan, self).__init__(tb, config)
        self.window = window
        self._dut_histo2 = self._dut_histo.Clone("test")

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #enable all pixels
        self.tb.testAllPixels(True)
        for dac in range((self.dac_max - self.dac_min)/self.step):
            self.vcals = []
            self.xrays = []
            self.tb.set_dac(self.scan_dac, self.dac_min + dac*self.step)
            #send a reset to the chip
            self.tb.pg_setup = [
                   ("resetroc",0)]    # pg_resr
            self.tb.set_pg(self.tb.pg_setup)
            self.tb.daq_enable()
            self.tb.pg_single(1,2)
            self.tb.daq_disable()
            #configure pg for efficiency test
            if self.dut.n_tbms > 0:
                self.tb.pg_setup = [
                    ("calibrate", self.cal_delay + self.tct_wbc),
                    ("trigger;sync", 0)]
            #Single roc
            else:
                self.tb.pg_setup = [
                    ("calibrate",self.cal_delay + self.tct_wbc), # PG_CAL
                    ("trigger",self.ttk),    # PG_TRG
                    ("token",0)]
            self.tb.set_pg(self.tb.pg_setup)

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
            self.dut.data = self.vcals
            #reduce to diducial volume
            self.dut.data = numpy.delete(numpy.delete(self.dut.data,79,2),[0,1,50,51],1)
            #abuse dut.ph_array container for xray hits
            self.dut.ph_array = self.xrays
            efficiency = self.dut.data.mean()*100/self.n_triggers
            self.eff.append(efficiency)
            self.logger.info('eff for %s = %i is %s' %(self.scan_dac, self.dac_min + dac*self.step, round(efficiency,2)))
            hitrate = (numpy.array(self.dut.ph_array).sum())/(self.triggers * 25e-9 * 1.0e6 * self.sensor_area)
            self.rate.append(hitrate)
            self.logger.info('rate for %s = %i is %s MHz/cm^2' %(self.scan_dac, self.dac_min + dac*self.step, round(hitrate, 2)))
            #clear data container for next scan step
            self.dut.data = numpy.zeros_like(self.dut.data)
            self.dut.ph_array = numpy.zeros_like(self.dut.ph_array)
            #send a reset to the chip
            self.tb.pg_setup = [
                    ("resetroc",0)]    # pg_resr
            self.tb.set_pg(self.tb.pg_setup)
            self.tb.daq_enable()
            self.tb.pg_single(1,2)
            self.tb.daq_disable()
                                  
        self.eff = numpy.array(self.eff)
        self.rate = numpy.array(self.rate)
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
        for roc in self.dut.rocs():
             plot = Plotter.create_tgraph2(self.eff, 'Efficiency of ROC %s'%roc.number, self.scan_dac, 'efficiency (%)',0, 255, self.step, self.dac_min)
             plot2 = Plotter.create_tgraph2(self.rate, 'Xray hit rate ROC %s'%roc.number, self.scan_dac, 'hit rate (MHz/cm^2)',0, 255, self.step, self.dac_min)
             self._histos.append(plot2)
             self._histos.append(plot)
             
    def restore(self):
        '''restore saved dac parameters'''
        super(HREfficiencyScan, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

