import logging
import time
import datetime
import dateutil.relativedelta
from plotter import Plotter

class Test(object):

    def __init__(self, tb, config = None):
        self.tb = tb
        self.dut = tb.dut
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.test = str(__name__)
        self.x_title = 'Column'
        self.y_title = 'Row'
        self._results = []
        self._histos = []

    def go(self, config):
        '''Called for every test, does prepare, run and cleanup.'''
        start_time = datetime.datetime.fromtimestamp(time.time())
        self.store(config)
        self.prepare(config)
        self.run(config)
        self.cleanup(config)
        self.restore(config)
        stop_time = datetime.datetime.fromtimestamp(time.time())
        delta_t = dateutil.relativedelta.relativedelta(stop_time, start_time)
        self.logger.info('Test finished after %.3f seconds' %delta_t.seconds)

    def store(self,config):
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

    def restore(self,config):
        '''restore saved dac parameters'''
        for roc in self.dut.rocs():
            for dac in roc.dacs():
                if dac.changed:
                    print dac.value, dac.stored_value
                    self.tb.set_dac_roc(roc,dac.number,dac.stored_value)
                    self.logger.info('restore %s'%dac)

    @property
    def results(self):
        return self._results
    
    @property
    def histos(self):
        return self._histos
