import numpy
import test
import ROOT
from plotter import Plotter

class CalibrateReadback(test.Test):
    ''' Calibrate readback of reg_ToCal to values of adc_CalTo, on a dac scan'''

    def prepare(self, config):
        self.dac = config.get('CalibrateReadback','dac')
        self.reg_val = config.get('CalibrateReadback','reg_ToCal')
        self.adc_CalTo = config.get('CalibrateReadback','adc_CalTo')
        self.delay = int(config.get('CalibrateReadback','delay'))
    
    def run(self, config):
        for roc in self.dut.rocs():
            rb = []
            adc = []
            for val in range(0,roc.dac(self.dac).range):
                self.tb.set_dac_roc(roc,self.dac,val)
                self.tb.m_delay(self.delay)
                rb_val = 256
                i=0
                while rb_val > 255 and i<10000:
                    rb_val = self.tb.decode_readback(int(self.reg_val))
                    i+=1
                #if rb_val < 255:
                rb.append(rb_val)
                self.tb.m_delay(self.delay)
                if self.adc_CalTo == 'ia': 
                    adc.append(self.tb.get_ia())
            roc.data = numpy.array(rb)
            plot_rb = Plotter.create_tgraph(roc.data, 'Readback register = %s vs DAC %s, ROC %s '%(self.reg_val,self.dac, roc.number), '%s [DAC]' %self.dac, 'rb [DAC]',0, roc.dac(self.dac).range)
            self._histos.append(plot_rb)
            roc.data = numpy.array(adc)
            plot_adc = Plotter.create_tgraph(roc.data, 'ADC %s vs DAC %s ROC %s '%(self.adc_CalTo, self.dac, roc.number), '%s [DAC]' %self.dac, 'Adc %s' %self.adc_CalTo ,0, roc.dac(self.dac).range)
            self._histos.append(plot_adc)
            f_rb = ROOT.TF1('lin_rb', '[0] + x*[1]', 20, 230)
            f_adc = ROOT.TF1('lin_adc', '[0] + x*[1]', 20, 230)
            plot_rb.Fit(f_rb)
            plot_adc.Fit(f_adc)
            frb0 = f_rb.GetParameter(0)
            frb1 = f_rb.GetParameter(1)
            fadc0 = f_adc.GetParameter(0)
            fadc1 = f_adc.GetParameter(1)
            config.set('ReadbackScan','rbFit_par0', str(frb0))
            config.set('ReadbackScan','rbFit_par1', str(frb1))
            config.set('ReadbackScan','adcFit_par0', str(fadc0))
            config.set('ReadbackScan','adcFit_par1', str(fadc1))
            self.restore()
            self.logger.debug('readbacks = %s'%rb)

    def cleanup(self, config):
        print('empty cleanup\n')
        #for roc in self.dut.rocs():
        #    plot = Plotter.create_tgraph(roc.data, 'Readback register = %s vs DAC %s, ROC %s '%(self.reg_val,self.dac, roc.number), '%s [DAC]' %self.dac, 'rb [DAC]',0, roc.dac(self.dac).range)
        #    self._histos.append(plot)
