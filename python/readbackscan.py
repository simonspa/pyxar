import numpy
import test
from plotter import Plotter

class ReadbackScan(test.Test):
    ''' Scan through a DAC while measuring the Readback for a given readback register value ''' 

    def prepare(self, config):
        self.dac = config.get('ReadbackScan','dac')
        self.reg_val = config.get('ReadbackScan','reg_val')
        self.delay = int(config.get('ReadbackScan','delay'))
    
    def run(self, config):
        for roc in self.dut.rocs():
            rb = []
            for val in range(0,roc.dac(self.dac).range):
                self.tb.set_dac_roc(roc,self.dac,val)
                self.tb.m_delay(self.delay)
                rb_val = 256
                i=0
                #for some values of DAC up to ~1000 iteration of readback needed to get good value
                while rb_val > 255 and i<10000:
                    rb_val = self.tb.decode_readback(int(self.reg_val))
                    i+=1
                rb.append(rb_val)
                self.tb.m_delay(self.delay)
            roc.data = numpy.array(rb)
            self.restore()
            self.logger.debug('readbacks = %s'%rb)

    def cleanup(self, config):
        for roc in self.dut.rocs():
            plot = Plotter.create_tgraph(roc.data, 'Readback register = %s vs DAC %s '%(self.reg_val,self.dac), '%s [DAC]' %self.dac, 'rb [DAC]',0, roc.dac(self.dac).range)
            self._histos.append(plot)
