import numpy
import test
from plotter import Plotter

class CurrentScan(test.Test):
    ''' Scan through a DAC while measuring the analog and digital currents of the ROC ''' 

    def prepare(self, config):
        self.dac = config.get('CurrentScan','dac')
        self.current = config.get('CurrentScan','current')
        self.delay = int(config.get('CurrentScan','delay'))
    
    def run(self, config):
        for roc in self.dut.rocs():
            current = []
            for val in range(0,roc.dac(self.dac).range):
                self.tb.set_dac_roc(roc,self.dac,val)
                if 'ana' in self.current:
                    current.append(self.tb.get_ia())
                elif 'dig' in self.current:
                    current.append(self.tb.get_id())
                self.tb.m_delay(self.delay)
            roc.data = numpy.array(current)
            self.restore()
            self.logger.debug('currents = %s'%current)

    def cleanup(self, config):
        for roc in self.dut.rocs():
            plot = Plotter.create_tgraph(roc.data, 'current %s of ROC %s'%(self.current,roc.number), self.dac, 'current',0, roc.dac(self.dac).range)
            self._histos.append(plot)
