import logging
import time
import os
import ROOT
from plotter import Plotter
import copy
from colorer import ColorFormatter

class Test(object):

    def __init__(self, tb, config = None, window = None):
        self.tb = tb
        self.dut = tb.dut
        self.config = config
        self.name = self.__class__.__name__
        self.directory = '%s/%s' %(self.config.get('General','work_dir'),self.name)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.logger = logging.getLogger(self.name)
        test_logger = logging.FileHandler('%s/test.log' %self.directory, mode='w')
        formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt='[%H:%M:%S]')
        test_logger.setFormatter(formatter)
        self.logger.addHandler(test_logger)
        self.test = str(self.__class__.__name__)
        self.x_title = 'Column'
        self.y_title = 'Row'
        self._results = []
        self._histos = []
        self.divider = 1
        if float(self.dut.n_rocs/8) > 1:
            self.divider = 2
        self._dut_histo = ROOT.TH2F(self.test, self.test, int(self.dut.n_rocs/self.divider*self.dut.roc(0).n_cols), 0., float(self.dut.n_rocs/self.divider*self.dut.roc(0).n_cols), int(self.divider*self.dut.roc(0).n_rows), 0., float(self.divider*self.dut.roc(0).n_rows))
        #self._dut_histo = ROOT.TH1F(self.test, self.test, 255, 0., 255)

    def fill_histo(self):
        for roc in self.dut.rocs():
            for pixel in roc.pixels():
                #Single ROC
                if self.dut.n_tbms == 0:
                    tmpCol = pixel.col+1
                    tmpRow = pixel.row+1
                #Module
                elif roc.number < 8:
                    tmpCol = int(self.dut.n_rocs/self.divider*roc.n_cols-(roc.number*roc.n_cols+pixel.col))
                    tmpRow = int(self.divider*roc.n_rows-pixel.row)
                else:
                    tmpCol = int(roc.number%(self.dut.n_rocs/self.divider)*roc.n_cols+pixel.col)+1
                    tmpRow = int(pixel.row+1)
                data1 = roc.data[pixel.col][pixel.row]
                #uncomment for ph live view 
                if data1 > 0:
                    self._dut_histo.SetBinContent(tmpCol, tmpRow, data1)
            
            #live view of PH
            #data_ph = self.dut.roc(0).ph_cal_array
            #data_ph_diff = data_ph[self.length:]
            #print data_ph_diff
            #self._dut_histo = ROOT.TH1F(self.test, self.test, 255, 0., 255)
            #for entry in range(len(data_ph_diff)):
            #    if data_ph_diff[entry] > 0:
            #        self._dut_histo.Fill(data_ph_diff[entry])
            #self.length += len(data_ph_diff)

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = time.time()
        self.store(config)
        self.prepare(config)
        self.run(config)
        self.cleanup(config)
        self.dump()
        self.restore()
        stop_time = time.time()
        delta_t = stop_time - start_time 
        self.logger.info('Test finished after %.1f seconds' %delta_t)

    def store(self, config):
        '''save dac parameters before test'''
        self.dut.store_dacs()

    def prepare(self, config):
        '''Fetch everything from config.'''
        pass

    def run(self, config): 
        '''Main test on DUT and TB.'''
        pass
    
    def cleanup(self, config):
        '''Convert test result data into histograms for display.'''
        for roc in self.dut.rocs():
            plot_dict = {'title':self.test+'_ROC_%s' %roc.number, 'x_title': self.x_title, 'y_title': self.y_title, 'data': roc.data}
            self._results.append(plot_dict)
        plot = Plotter(self.config, self)
        for roc in self.dut.rocs():
            th1 = Plotter.create_th1(roc.data,self.test+'_Distribution_ROC_%s' %(roc.number), 'Projection of test', '# pixels')
            self._histos.append(th1)
        self._histos.extend(plot.histos)
        self.fill_histo()
        self._histos.append(self._dut_histo)

    def restore(self):
        '''restore saved dac parameters'''
        for roc in self.dut.rocs():
            for dac in roc.dacs():
                if dac.changed:
                    self.tb.set_dac_roc(roc,dac.number,dac.stored_value)
                    self.logger.info('restore %s'%dac)
    
    def dump(self):
        '''Dump results in folder'''
        #Write config
        config_file = open('%s/config' %(self.directory), 'w')
        self.config.write(config_file)
        config_file.close()
        #Write ROC settings
        for roc in self.dut.rocs():
            roc.save('', self.directory)
        #Write HISTOS
        #TODO does RECREATE make sense?
        a_file = ROOT.TFile('%s/result.root' %(self.directory), 'RECREATE' )
        for histo in self._histos:
            histo.Write()
        a_file.Close()

    @property
    def results(self):
        return self._results
    
    @property
    def histos(self):
        return self._histos
