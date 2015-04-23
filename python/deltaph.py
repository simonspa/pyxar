import test
import numpy
import ROOT
from plotter import Plotter
import random

class DeltaPH(test.Test):
    ''' measure difference of pulse height for Vcal 50 L and Vcal255 H for all PHScale - PHOffset combinations for a given amount of pixels to measure maximum PH coverage in the ADC space
    single ROCs only at the moment'''

    def prepare(self, config):
        self.vcalhigh = 255
        self.vcallow = 60
        
        self.n_triggers = int(config.get('DeltaPH','n_triggers'))
        self.n_pixels = int(config.get('DeltaPH','n_pixels'))
        shape = (256,256)
        self.delta_ph_sum = numpy.zeros(shape)    
        self.phmin_sum = numpy.zeros(shape)    
        self.phmax_sum = numpy.zeros(shape)    
        self.count = 0
        self.count_dead = 0
        
    def run(self, config):
        self.tb.m_delay(15000)
        self.logger.info('Running delta PH measurement. Please execute test with trimmed sample')
        #Disabling all pixels
        for roc in self.dut.rocs():
            self.tb.testAllPixels(False)
            roc.pixel(5,5).active = False
            self.logger.info('Measuring %s' %roc)
            for pix in range(self.n_pixels):
                #draw a random number between 0 and 1
                seed_col = random.random()
                seed_row = random.random()
                #convert this seed to a valid col and row
                col = int(seed_col*52)
                row = int(seed_row*80)
                self.count += 1
                print 'testing pixel %i %i (number %i out of %i pixels to be tested' %(col, row, self.count, self.n_pixels)
                #Enabling pixel under test
                test_pixel = roc.pixel(col, row)
                test_pixel.active = True
                #set Vcal 50 low range and measure ph in phscale phoffset space
                self.tb.set_dac_roc(roc, 'Vcal', self.vcallow)
                self.tb.set_dac_roc(roc, 'CtrlReg', 0)
                self.tb.get_ph_dacdac(1,'VOffsetR0','VIref_ADC')
                for pixel in roc.active_pixels():
                    self.phmin = pixel.data 
                #set Vcal 255 high range and measure ph in phscale phoffset space
                self.tb.set_dac_roc(roc, 'Vcal', self.vcalhigh)
                self.tb.set_dac_roc(roc, 'CtrlReg', 4)
                self.tb.get_ph_dacdac(1,'VOffsetR0','VIref_ADC')
                for pixel in roc.active_pixels():
                    self.phmax = pixel.data
                #substract phmin from phmax to find delta ph
                self.delta_ph = self.phmax - self.phmin
                if numpy.sum(self.phmin) == 0 and numpy.sum(self.phmax) == 0:
                    self.count_dead += 1
                #add arrays to sum array in order to calculate pixel average phs
                self.phmin_sum += self.phmin
                self.phmax_sum += self.phmax
                self.delta_ph_sum += self.delta_ph
                test_pixel.active = False
        #reset CtrlReg
        self.tb.set_dac_roc(roc, 'CtrlReg', 0)
        #disable all pixels
        self.tb.testAllPixels(False)
        self.logger.info('%i pixel average maximum delta PH is %s ADC counts' %(self.count-self.count_dead, numpy.amax(self.delta_ph_sum/float(self.count-self.count_dead))))
        #self.logger.info('maximum delta PH found for PHScale = %i and PHOffset %i' %())


    def cleanup(self, config):
        plot = Plotter(self.config, self)
        for roc in self.dut.rocs():
            minPH_histo = Plotter.create_th2(self.phmin_sum/float(self.count-self.count_dead), 256, 256,'%i pixel average phmin' %(self.count-self.count_dead), 'PHOffset', 'PHScale')
            self._histos.append(minPH_histo)
            maxPH_histo = Plotter.create_th2(self.phmax_sum/float(self.count-self.count_dead), 256, 256,'%i pixel average phmax' %(self.count-self.count_dead), 'PHOffset', 'PHScale') 
            self._histos.append(maxPH_histo)
            deltaPH_histo = Plotter.create_th2(self.delta_ph_sum/float(self.count-self.count_dead), 256, 256, '%i pixel average Delta PH' %(self.count-self.count_dead), 'PHOffset', 'PHScale')
            self._histos.append(deltaPH_histo)
 
















