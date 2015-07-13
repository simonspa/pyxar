import test
import time
import ROOT
import numpy
from plotter import Plotter
import random

class HldDelay(test.Test):
    ''' make a phscan using the VhldDel DAC with n calibrates 
    for all pixels in one randomly picked DCol and plot VhldDel 
    value where minimum of the PH occurs as function of the 
    pixel position. This test allows to determine how far the 
    ColOr wave propagates in 25ns'''

    def prepare(self, config):
        #read in test parameters
        self.n_triggers = 10
        self.dac = 'VhldDel'
        self.n_rocs = int(config.get('Module','rocs'))
        self.cal_delay = int(config.get('Testboard','pg_cal'))
        self.tct_wbc = int(config.get('Testboard','tct_wbc'))
        self.n_rocs = int(config.get('Module','rocs'))
        self.ttk = 16
        self.ph = []
        self.dip = []
        self.jumps = []
        self.shape = (26,160)
        self.result = numpy.zeros(self.shape)



        for roc in self.dut.rocs():
            roc.pixel(5,5).active = False

    #def __init__(self, tb, config, window):
    #    super(HldDelay, self).__init__(tb, config)
    #    self.window = window
    #    self._dut_histo2 = self._dut_histo.Clone("test")


    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.start_data = time.time()
        #reset data containers
        self.dut.data = numpy.zeros_like(self.dut.data)
        for roc in self.dut.rocs():
            #loop over double columns
            for icol in range(2):
                icol +=7
                #loop over all pixels of the dcol and make a phscan using the VhldDel DAC
                for irow in range(160):
                    if irow < 80:
                        row = irow
                        col = icol*2
                    else:
                        row = -irow+159
                        col = icol*2+1
                    #arm pixel to be tested
                    if self.n_rocs>1:
                        self.logger.warning('Test not compatible with DUT with more than 1 ROC - aborting')
                        break
                    roc.pixel(col,row).active = True
                    self.tb.get_ph_dac(self.n_triggers, self.dac)
                    for roc in self.dut.rocs():
                        for pixel in roc.active_pixels():
                            self.ph = pixel.data
                            self.result[icol][irow] = numpy.argmin(numpy.array(pixel.data))
                    roc.pixel(col,row).active = False
        
        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time
        self.logger.info('Test finished after %.1f seconds' %delta_t)
       
       
        ''' 
        vhlddel = self.dip[0]
        for pix in range(len(self.dip)):
            vhlddel_tmp = self.dip[pix]
            if vhlddel > vhlddel_tmp+4:
                self.jumps.append(pix)
            vhlddel = self.dip[pix]

        self.logger.info('----------------------------------------')
        if len(self.jumps)==2:
            delta1 = self.jumps[1]-self.jumps[0]
            self.logger.info('jump in VhldDel at pixels %s and %s' %(self.jumps[0], self.jumps[1]))
            self.logger.info('speed of ColOr wave is %i pixels per 25 ns' %delta1)
        elif len(self.jumps)==3:
            delta1 = self.jumps[1]-self.jumps[0]
            delta2 = self.jumps[2]-self.jumps[1]
            self.logger.info('jump in VhldDel at pixels %s, %s and %s' %(self.jumps[0], self.jumps[1], self.jumps[2]))
            self.logger.info('speed of ColOr wave is %i pixels per 25 ns' %delta1)
            self.logger.info('speed of ColOr wave is %i pixels per 25 ns' %delta2)
        elif len(self.jumps)==1:
            self.logger.info('only one jump in VhldDel registered')
        elif len(self.jumps)==0:
            self.logger.info('no jump in VhldDel registered')
        else:
            self.logger.info('more than two jumps in VhldDel registered')
        self.logger.info('----------------------------------------')
        '''


    def cleanup(self, config):
        #plot2 = Plotter.create_tgraph(self.ph, 'title', self.dac, 'Pulseheight', 0, 255)
        #self._histos.append(plot2)
        #plot = Plotter.create_tgraph(self.dip, 'double colum number %i' %self.dcol, 'pixel', self.dac, 0, len(self.dip))
        #self._histos.append(plot)
        res = Plotter.create_th2(self.result,26, 160, "VhldDel dip", "dcol", "pixel")
        self._histos.append(res)
   
    
    def restore(self):
        '''restore saved dac parameters'''
        super(HldDelay, self).restore()
        for roc in self.dut.rocs():
            roc.ph_array = [0]
            roc.ph_cal_array = [0]
        self.dut.data = numpy.zeros_like(self.dut.data)

