import time
import numpy
import ROOT
import test
from plotter import Plotter

class HRTest(test.Test):

    def __init__(self, tb, config, window):
        super(HRTest, self).__init__(tb, config)
        self.window = window
        self.start_data = 0
        self.data_taking_time = 5
        self.period = 1288
        self.average_ph = numpy.copy(self.dut.data)
        if self.window:
            self.window.histos.extend([self._dut_histo])

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        self.length=0
        for measurement_time in range(self.data_taking_time):
            self.tb.pg_loop(self.period)
            self.tb.m_delay(1000)
            self.tb.pg_stop()
            self.take_data(config)
            print 'remaining measurement time %i seconds' %(self.data_taking_time - measurement_time)
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
        '''Main test on DUT and TB.'''
        time_left = self.data_taking_time - (time.time() - self.start_data)
        n_hits, average_ph, ph_histogram, ph_cal_histogram, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=True)
        self.dut.data += n_hits
        n_rocs = int(config.get('Module','rocs'))
        for roc in range(n_rocs):
            self.dut.ph_array[roc].extend(ph_histogram[roc])
            self.dut.ph_cal_array[roc].extend(ph_cal_histogram[roc])
        self.update_histo()
           
    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        #Create PH histograms for every ROC and whole DUT
        for roc in self.dut.rocs():
            ph_adc = numpy.array(self.dut.ph_array[roc.number])
            ph_vcal = numpy.array(self.dut.ph_cal_array[roc.number])
            PH_ADC = Plotter.create_th1(ph_adc,'PH_ADC_ROC_%s' %roc.number, 'ADC units', '# entries', 0, 255)
            PH_VCAL = Plotter.create_th1(ph_vcal,'PH_VCAL_ROC_%s' %roc.number, 'Vcal units', '# entries', 0, 255)
            self._histos.append(PH_ADC)
            self._histos.append(PH_VCAL)

        self._histos.extend(plot.histos)
        #calculating results
        for roc in self.dut.rocs():
            ia = self.tb.get_ia()
            self.logger.info('%s: ia = %.2f' %(roc, ia))
            id = self.tb.get_id()
            self.logger.info('%s: id = %.2f' %(roc, id))
        self._n_rocs = int(config.get('Module','rocs'))
        sensor_area = self._n_rocs * 52 * 80 * 0.01 * 0.015 #in cm^2
        self.logger.debug('number of rocs %s' %self._n_rocs)
        self.logger.debug('sensor area %s' %round(sensor_area,2))
        hits = numpy.sum(self.dut.data)
        trigger_rate = 1.0e6 / (25.0 * self.period)
        rate = hits / (self.data_taking_time * trigger_rate * 1e3 * 25e-9 * self.scc * 1.0e6 * sensor_area)    

        self.logger.info('data aquisition time    %i' %self.data_taking_time)
        self.logger.info('number of hits          %i' %hits)
        self.logger.info('trigger rate            %s kHz' %round(trigger_rate,1))
        self.logger.info('hit rate                %s MHz/cm^2' %round(rate,6))
        self.logger.info('scc                     %i ' %self.scc)
       

        self._histos.extend([self._dut_histo])
        if self.window:
            self.window.histos.pop()

    def restore(self):
        '''restore saved dac parameters'''
        super(HRTest, self).restore()
        self.tb.daq_disable()
        self.tb.pg_stop()
        self.tb.init_pg(self.config)
        self.tb.init_deser()
