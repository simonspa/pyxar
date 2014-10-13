import test
import numpy
import ROOT
from plotter import Plotter

class Timewalk(test.Test):
    ''' measuring the timewalk, i.e. the timing difference between the smallest and the largest Vcal signals visible. The conversion from CalDel units to nano seconds is based on the width of the efficiency window which corresponds to 25 ns '''
    def prepare(self, config):
        self.n_triggers = int(config.get('Timewalk','n_triggers'))
        self.caldel_margin = 10
        self.vcal_margin = 5
        self.caldel1 = []
        self.caldel2 = []
        self.caldel4 = []
        self.caldel_width = []
        self.delta_caldel = []
        self.timewalk = []
        for roc in self.dut.rocs():
            self.caldel1.append([])
            self.caldel2.append([])
            self.caldel4.append([])
            self.delta_caldel.append([])
            self.timewalk.append([])
            self.caldel_width.append([])

    def run(self, config):
        self.logger.info('Running timewalk measurement. Please execute test with trimmed sample')
        #Disabling all pixels
        self.tb.testAllPixels(False)
        for roc in self.dut.rocs():
            self.logger.info('Measuring %s' %roc)
            for col in range(7):
                for row in range(7):
                    #Enabling pixel under test
                    roc.pixel(col,row).active = True
                    #set Vcal 255 high range to measure efficiency window width
                    self.tb.set_dac_roc(roc, 'Vcal', 255)
                    self.tb.set_dac_roc(roc, 'CtrlReg', 4)
                    #search for begin of efficiency window
                    thr1 = self.tb.get_pixel_threshold(roc, col, row, self.n_triggers, 'CalDel', 50, False, False, False)
                    self.caldel1[roc.number].append(thr1)
                    #search for end of efficiency window
                    thr2 = self.tb.get_pixel_threshold(roc, col, row, self.n_triggers, 'CalDel', 50, False, False, True)
                    self.caldel2[roc.number].append(thr2)
                    #calculate width of efficiency window
                    delta_thr = thr2 - thr1
                    self.caldel_width[roc.number].append(delta_thr)
                    conversion = delta_thr / 25
                    #reset CtrlReg
                    self.tb.set_dac_roc(roc, 'CtrlReg', 0)
                    #find the smalles CalDel value for which 50% of the triggers                     #can be seen at any Vcal value
                    for i in range(50):
                        if thr1-50 > 0:
                            caldel = thr1 - 50 + i
                        else:
                            caldel = i
                        self.tb.set_dac_roc(roc, 'CalDel', caldel)
                        thr3 = self.tb.get_pixel_threshold(roc, col, row, self.n_triggers, 'Vcal', 50, False, False, False)
                        if (thr3 != 255 and thr3 != 0): 
                            break
                    #append found caldel value
                    self.caldel4[roc.number].append(caldel)
                    #calculate timewalk
                    timewalk_caldel = thr1 - caldel
                    self.delta_caldel[roc.number].append(timewalk_caldel)
                    timewalk_time = timewalk_caldel / conversion
                    self.timewalk[roc.number].append(timewalk_time)
                    #disable pixel under test
                    roc.pixel(col,row).active = False
                    if col==0 and row ==0:
                        self.logger.debug('caldel1      = %i' %thr1)
                        self.logger.debug('caldel2      = %i' %thr2)
                        self.logger.debug('caldel width = %i' %delta_thr)
                        self.logger.debug('caldel4      = %i' %caldel)
                        self.logger.debug('timewalk dac = %i' %timewalk_caldel)
                        self.logger.debug('timewalk ns  = %i' %timewalk_time)
        #convert to numpy arrays
        self.array1=numpy.array(self.caldel1)
        self.array2=numpy.array(self.caldel2)
        self.array4=numpy.array(self.caldel4)
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
            caldel4_histo = Plotter.create_th1(self.array4[roc.number],'CalDel4_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(caldel4_histo)
            timewalk_caldel_histo = Plotter.create_th1(self.array5[roc.number],'Timewalk_CalDel_units_distribution_%s' %roc, 'CalDel', '# pixels',1,255)
            self._histos.append(timewalk_caldel_histo)
            timewalk_histo = Plotter.create_th1(self.array7[roc.number],'Timewalk_distribution_%s' %roc, 'Timewalk (ns)', '# pixels',1,40)
            self._histos.append(timewalk_histo)
            


















