import time
import numpy
import ROOT
import test
from plotter import Plotter

class HotPixelMasker(test.Test):
    '''Measure background hitmap and automatically generate the MaskFile.dat to mask noisy pixels. Use 'noise' parameter to adjust number of tolerated noise hits per pixel.'''

    def prepare(self, config):
        self.data_taking_time = int(config.get('HotPixelMasker','data_taking_time'))
        ttk = int(config.get('HotPixelMasker','ttk'))
        self.noise = int(config.get('HotPixelMasker','noise'))
        self.period = int(config.get('HotPixelMasker','period'))
        for roc in self.dut.rocs():
            self.tb.select_roc(roc)
            for col in range(roc.n_cols):
                self.tb.enable_column(col)
        self.tb.pg_stop()
        self.tb.init_deser()
        self.tb.daq_enable()
        self.tb.pg_setcmd(0, self.tb.PG_RESR)
        self.tb.pg_single()
        if self.dut.n_tbms > 0:
            self.tb.init_pg(self.config)
            #self.tb.pg_setcmd(0, self.tb.PG_RESR + 15)
            #self.tb.pg_setcmd(1, self.tb.PG_CAL + 56)
            #self.tb.pg_setcmd(0, self.tb.PG_SYNC + self.tb.PG_TRG)
            #self.tb.pg_setcmd(1, self.tb.PG_TRG  + ttk)
        else:
            self.tb.pg_setcmd(0, self.tb.PG_TRG  + ttk)
            self.tb.pg_setcmd(1, self.tb.PG_TOK)

    def __init__(self, tb, config, window):
        super(HotPixelMasker, self).__init__(tb, config)
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
        self.logger.warning('Do not expose ROC or module to X-rays or particles during this test!')
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
        n_hits, average_ph, ph_histogram, ph_cal_histogram, nhits_vector, ph_vector, addr_vector = self.tb.get_data(Vcal_conversion=False)
        self.dut.data += n_hits
        n_rocs = int(config.get('Module','rocs'))
        self.update_histo()
           
    def cleanup(self, config):
        '''Convert test result data into histograms for display and writes pixel mask file.'''
        self.fill_histo()
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': self.dut.data[roc.number]}
            self._results.append(plot_dict)
            plot = Plotter(self.config, self)
        self._histos.extend(plot.histos)

        #find noise hits in hitmap and write MaskFile.dat
        path = self.directory.replace('/HotPixelMasker','')
        outfile = open('%s/MaskFile.dat' %(path), 'w')
        noisy_tot = 0
        self.logger.info('List of detected hot pixels:')
        self.logger.info('--------------------------------------------------')
        for roc in self.dut.rocs():
            for col in range(roc.n_cols):
                for row in range(roc.n_rows):
                    noise_hits = self._histos[roc.number].GetBinContent(col+1,row+1)
                    if noise_hits > self.noise:
                        noisy_tot += 1
                        self.logger.info('Found noisy pixel %i:%i in %s with %i noise hits' %(col, row, roc, noise_hits))
                        outfile.write('pix %i %i %i\n'%(roc.number, col, row))
        self.logger.info('--------------------------------------------------')
        self.logger.info('Masked %i noisy pixel in total' %(noisy_tot))
        outfile.close()
        self.logger.info("Created new mask file 'MaskFile.dat' for DUT in %s" %path)

        n_rocs = int(config.get('Module','rocs'))
        #print warning if more than 1 per mil of pixels in dut are noisy
        if noisy_tot > (n_rocs*4160./1000):
            self.logger.warning('More than one per mil of all pixels in dut are noisy! Make sure dut is not exposed to any radiation and check setup grounding.')


        self._histos.extend([self._dut_histo])
        if self.window:
            self.window.histos.pop()

    def restore(self):
        '''restore saved dac parameters'''
        super(HotPixelMasker, self).restore()
        self.tb.daq_disable()
        self.tb.pg_stop()
        self.tb.init_pg(self.config)
        self.tb.init_deser()

