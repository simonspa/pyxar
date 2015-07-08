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
    it is iterated over all pixels of the dcol. In each iteration both active pixels 
    are pulsed and the ph is measured. For the fixed pixel this ph is measured as a 
    function of the position of the pixel in dcol B. Constant ph is expected for a 
    range of n pixel positions equal to the distance the wave travels in 25 ns'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = 100
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = int(config.get('Testboard','pg_cal'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.n_rocs = int(config.get('Module','rocs'))
        self.ttk = 16
        self.ph_fix = []    #ph's of the fixed pixel
        self.ph_it = []     #ph's of the interative pixel
        self.jumps = []

        for roc in self.dut.rocs():
            roc.pixel(5,5).active = False

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #reset data containers
        self.dut.data = numpy.zeros_like(self.dut.data)
        for roc in self.dut.rocs():
            #pick a fixed pixel in dcol A
            colA = 10
            rowA = 40
            #pick dcol B
            col = 20
            #loop over all pixels of the dcol B and pulse both pixels
            for irow in range(160):
                if irow < 80:
                    rowB = irow
                    colB = col
                else:
                    rowB = -irow+159
                    colB = col+1
                #abort if more than one ROC
                if self.n_rocs>1:
                    self.logger.warning('Test not compatible with DUT with more than 1 ROC - aborting')
                    break
                #arm the two pixels
                self.tb.testAllPixels(False)
                self.tb.testPixel(colA, rowA, True, 0)
                self.tb.testPixel(colB, rowB, True, 0)
                print 'testing pixels %i:%i and %i:%i' %(colA, rowA, colB, rowB) 
                datas = self.tb.getPulseheightMap(0x0, self.n_triggers)
                for px in datas:
                    if px.column == colA and px.row == rowA:
                        self.ph_fix.append(px.value)
                    elif px.column == colB and px.row == rowB:
                        self.ph_it.append(px.value)
                    else: 
                        self.logger.warning('Found hit in unexpected pixel!')
                self.tb.testAllPixels(False)

        if not len(self.ph_fix) == len(self.ph_it):
            self.logger.warning('Different number of hits in fixed and iterative pixel! - aborting')
            return

        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)
        
    def cleanup(self, config):
        plot = Plotter.create_tgraph(self.ph_fix, 'PH of fixed pixel', 'position of iterative pixel', 'pulseheight (ADC)', 0, len(self.ph_fix))
        self._histos.append(plot)
        plot2 = Plotter.create_tgraph(self.ph_it, 'PH of iterative pixel', 'position of iterative pixel', 'pulseheight (ADC)', 0, len(self.ph_fix))
        self._histos.append(plot2)
   
    def restore(self):
        '''restore saved dac parameters'''
        super(ColOrWave, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
            self.ph_fix = []
            self.ph_it = []
        self.dut.data = numpy.zeros_like(self.dut.data)

