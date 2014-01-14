import logging
import time
import os
import ROOT
from plotter import Plotter

class Test(object):

    def __init__(self, tb, config = None):
        self.tb = tb
        self.dut = tb.dut
        self.config = config
        self.name = self.__class__.__name__
        self.directory = '%s/%s' %(self.config.get('General','work_dir'),self.name)
        self.logger = logging.getLogger(self.name)
        self.test = str(self.__class__.__name__)
        self.x_title = 'Column'
        self.y_title = 'Row'
        self._results = []
        self._histos = []

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
            th1 = Plotter.create_th1(roc.data,'ROC_%s' %(roc.number), 'Projection of test', '# pixels')
            self._histos.append(th1)
        self._histos.extend(plot.histos)

    def restore(self):
        '''restore saved dac parameters'''
        for roc in self.dut.rocs():
            for dac in roc.dacs():
                if dac.changed:
                    self.tb.set_dac_roc(roc,dac.number,dac.stored_value)
                    self.logger.info('restore %s'%dac)
    
    def dump(self):
        '''Dump results in folder'''
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
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
