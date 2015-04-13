import test
import numpy
import ROOT
from plotter import Plotter
import random

class Timewalk(test.Test):
    ''' measuring the timewalk, i.e. the timing difference between the smallest and the largest Vcal signals visible. The conversion from CalDel units to nano seconds is based on the width of the efficiency window which corresponds to 25 ns '''
    def prepare(self, config):
        #dose 0
#        self.vcalhigh = 255
#        self.vcallow = 50
        #dose 60
        self.vcalhigh = 229
        self.vcallow = 45
        #dose 120
#        self.vcalhigh = 227
#        self.vcallow = 45
        #dose 180
#        self.vcalhigh = 225
#        self.vcallow = 44
        #dose 240
#        self.vcalhigh = 225
#        self.vcallow = 44
        #dose 480
#        self.vcalhigh = 224
#        self.vcallow = 44
        

        
        self.n_triggers = int(config.get('Timewalk','n_triggers'))
        self.n_pixels = int(config.get('Timewalk','n_pixels'))
        self.caldel_margin = 10
        self.vcal_margin = 5
        self.caldel1 = []
        self.caldel2 = []
        self.caldel3 = []
        self.caldel_width = []
        self.delta_caldel = []
        self.timewalk = []
        self.scanrange = 90
        for roc in self.dut.rocs():
            self.caldel1.append([])
            self.caldel2.append([])
            self.caldel3.append([])
            self.delta_caldel.append([])
            self.timewalk.append([])
            self.caldel_width.append([])
            self.count = 0

    def run(self, config):
        self.tb.m_delay(15000)
        self.logger.info('Running timewalk measurement. Please execute test with trimmed sample')
        #Disabling all pixels
        self.tb.testAllPixels(False)
        for roc in self.dut.rocs():
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
                #set Vcal 255 high range to measure efficiency window width
                self.tb.set_dac_roc(roc, 'Vcal', self.vcalhigh)
                self.tb.set_dac_roc(roc, 'CtrlReg', 4)
                #search for begin of efficiency window
                thr1 = self.tb.get_pixel_threshold(roc, col, row, self.n_triggers, 'CalDel', 50, False, False, False)
                if not thr1 == None:
                    self.caldel1[roc.number].append(float(thr1))
                #search for end of efficiency window
                thr2 = self.tb.get_pixel_threshold(roc, col, row, self.n_triggers, 'CalDel', 50, False, False, True)
                if not thr2 == None:
                    self.caldel2[roc.number].append(float(thr2))
                #calculate width of efficiency window
                if thr2 == None or thr1 == None:
                    delta_thr = 0
                else:
                    delta_thr = thr2 - thr1
                self.caldel_width[roc.number].append(delta_thr)
                conversion = delta_thr / 25
                #reset CtrlReg
                self.tb.set_dac_roc(roc, 'CtrlReg', 0)
                #measure caldel threshold for small Vcal signal
                self.tb.set_dac_roc(roc, 'Vcal', self.vcallow)
                thr3 = self.tb.get_pixel_threshold(roc, col, row, self.n_triggers, 'CalDel', 50, False, False, False)
                if not thr3 == None:
                    self.caldel3[roc.number].append(float(thr3))
                #calculate timewalk
                if thr3 == None: 
                    continue
                else:
                    timewalkCaldel = thr1 - thr3
                self.delta_caldel[roc.number].append(timewalkCaldel)
                timewalk_time = timewalkCaldel / conversion
                self.timewalk[roc.number].append(timewalk_time)
               
                #disable pixel under test
                roc.pixel(col,row).active = False
        #convert to numpy arrays
        self.array1=numpy.array(self.caldel1)
        self.array2=numpy.array(self.caldel2)
        self.array3=numpy.array(self.caldel3)
        self.array5=numpy.array(self.delta_caldel)
        self.array7=numpy.array(self.timewalk)
        self.array8=numpy.array(self.caldel_width)
        #disable all pixels
        self.tb.testAllPixels(False)
                    
        

    def cleanup(self, config):
        plot = Plotter(self.config, self)
        for roc in self.dut.rocs():
            caldel1_histo = Plotter.create_th1(self.array1[roc.number],'CalDel1_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(caldel1_histo)
            caldel2_histo = Plotter.create_th1(self.array2[roc.number],'CalDel2_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(caldel2_histo)
            caldel_width_histo = Plotter.create_th1(self.array8[roc.number],'CalDel_width_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(caldel_width_histo)
            caldel3_histo = Plotter.create_th1(self.array3[roc.number],'CalDel3_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(caldel3_histo)
            timewalk_caldel_histo = Plotter.create_th1(self.array5[roc.number],'Timewalk_CalDel_units_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(timewalk_caldel_histo)
            timewalk_histo = Plotter.create_th1(self.array7[roc.number],'Timewalk_distribution_%s' %roc, 'Timewalk (ns)', '# pixels',0,100)
            self._histos.append(timewalk_histo)
            


















