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
        self.logger.debug('ia = %s'%self.tb.getTBia())

        self.tb.m_delay(15000)
        for roc in self.dut.rocs():
            current = []
            # Let settle current at DCA_low:
            self.tb.set_dac_roc(roc,self.dac,0)
            self.tb.m_delay(100)
            for val in range(0,roc.dac(self.dac).range):
                self.tb.set_dac_roc(roc,self.dac,val)
                self.tb.m_delay(self.delay)
                if 'ana' in self.current:
                    current.append(self.tb.getTBia()*1000)
                elif 'dig' in self.current:
                    current.append(self.tb.getTBid()*1000)
            roc.data = numpy.array(current)
            self.tb.m_delay(self.delay)
            self.restore()
            self.logger.debug('currents = %s'%current)

    def cleanup(self, config):
        for roc in self.dut.rocs():
            plot = Plotter.create_tgraph(roc.data, 'current %s of ROC %s'%(self.current,roc.number), self.dac, 'current',0, roc.dac(self.dac).range)
            self._histos.append(plot)
