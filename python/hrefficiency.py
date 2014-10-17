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
        self.resr_delay = int(config.get('Testboard','pg_resr'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.ttk = int(config.get('HREfficiency','ttk'))
        
        #containers to hold vcal and xray hits
        self.vcals = []
        self.xrays = []
        self.shape = (52,80)
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
                #("resetroc", resr_delay),
                ("calibrate", self.cal_delay + self.tct_wbc),
                ("trigger;sync", 0)]
        #Single roc
        else:
            self.tb.pg_setup = [
                ("calibrate",self.cal_delay + self.tct_wbc), # PG_CAL
                ("trigger",self.ttk),    # PG_TRG
                ("token",0)]
        self.tb.set_pg(self.tb.pg_setup)

    def __init__(self, tb, config, window):
        super(HREfficiency, self).__init__(tb, config)
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
        #abuse dut.ph_array container for xray hits
        self.dut.ph_array = self.xrays
      
        #send a reset to the chip
        self.tb.pg_setup = [
                ("resetroc",0)]    # pg_resr
        self.tb.set_pg(self.tb.pg_setup)
        self.tb.daq_enable()
        self.tb.pg_single(1,2)
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

    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s_Vcal_hits' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot_dict = {'title':self.test+'_ROC_%s_Xray_hits' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.ph_array[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)
        self._histos.extend([self._dut_histo])
        self._histos.extend([self._dut_histo2])

        #extracting efficiency
        eff_mean = []
        eff_rms = []
        pixel_zero_eff = 0
        for roc in self.dut.rocs():
            eff_list = []
            eff_list_fiducial = []
            for col in range(roc.n_cols):
                for row in range(roc.n_rows):
                    eff_list.append((self._histos[roc.number].GetBinContent(col+1, row+1)*100)/self.n_triggers)
                    if not (col == 0 or col == 1 or col == 50 or col == 51 or row == 79):
                        if not self._histos[roc.number].GetBinContent(col+1,row+1) == 0:
                            eff_list_fiducial.append((self._histos[roc.number].GetBinContent(col+1, row+1)*100)/self.n_triggers)
                        else:
                            pixel_zero_eff += 1
            eff_arr = numpy.asarray(eff_list)
            eff_arr_fiducial = numpy.asarray(eff_list_fiducial)
            eff = Plotter.create_th1(eff_arr, 'efficiency_ROC_%s' %roc.number, 'efficiency (%)', '# entries', 0, 101)
            eff_fiducial = Plotter.create_th1(eff_arr_fiducial, 'fiducial_efficiency_ROC_%s' %roc.number, 'efficiency (%)', '# entries', 0, 101)
            self._histos.append(eff)
            self._histos.append(eff_fiducial)
            eff_mean.append(eff_fiducial.GetMean())
            eff_rms.append(eff_fiducial.GetRMS())


        #rate calculation
        sensor_area = self.n_rocs * 52 * 80 * 0.01 * 0.015 #in cm^2
        self.logger.info('number of rocs            %s' %self.n_rocs)
        self.logger.info('sensor area               %s cm^2' %round(sensor_area,2))
        xray_hits = numpy.sum(self.dut.ph_array)
        triggers = self.n_rocs * 4160 * self.n_triggers
        rate = xray_hits / (triggers * 25e-9 * 1.0e6 * sensor_area)
        self.logger.info('number of xray hits       %i' %xray_hits)
        self.logger.info('total number of triggers  %i' %triggers)
        self.logger.info('xray hit rate             %s MHz/cm^2' %round(rate,6))
        self.logger.info('-----------------------------------')
        self.logger.info('ROC efficiencies in fuducial volume:')
        for roc in range(self.n_rocs):
            self.logger.info('ROC %i:   %s +/- %s' %(roc, round(eff_mean[roc],2), round(eff_rms[roc],2)))
        self.logger.info('-----------------------------------')
        self.logger.warning('%i pixels in whole DUT with 0 efficiency!' %pixel_zero_eff)

    def restore(self):
        '''restore saved dac parameters'''
        super(HREfficiency, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

