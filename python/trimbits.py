import test
import numpy
import ROOT
from plotter import Plotter

class TrimBits(test.Test):
    ''' test individual trimbits (4) for each pixel by calculating difference in threshold for bit turned on and off '''
    
    def prepare(self, config): 
        self.vcal = int(config.get('TrimBits','Vcal'))
        self.cals = 0
        self.xtalk = 0
        self.reverse = 0
        self.dac = 'VthrComp'
        self.n_triggers = int(config.get('TrimBits','n_triggers'))
        self.vtrim15 = int(config.get('TrimBits','Vtrim15'))
        self.vtrim14 = int(config.get('TrimBits','Vtrim14'))
        self.vtrim13 = int(config.get('TrimBits','Vtrim13'))
        self.vtrim11 = int(config.get('TrimBits','Vtrim11'))
        self.vtrim7 = int(config.get('TrimBits','Vtrim7'))
        self.vtrims = [self.vtrim15, self.vtrim14, self.vtrim13, self.vtrim11, self.vtrim7]
        self.trim_bit = [15,14,13,11,7]
        self.vthr_dists = []

    def run(self, config): 
        self.logger.info('Running trim bit test')
        self.tb.set_dac('Vcal', self.vcal)
        for step, bit in enumerate(self.trim_bit):
            trim_bits = self.dut.trim
            self.logger.info('Trimming DUT to %s' %bit)
            numpy.clip(trim_bits, bit, bit, out=trim_bits)
            self.tb.trim(trim_bits)
            self.tb.set_dac('Vtrim', self.vtrims[step])
            dut_thr_map = self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse) 
            self.vthr_dists.append(dut_thr_map)

    def cleanup(self, config):
        color_dict = [ROOT.kYellow,ROOT.kBlack,ROOT.kRed,ROOT.kBlue,ROOT.kGreen]
        plot = Plotter(self.config, self)
        for roc in self.dut.rocs():
            min_axis = numpy.amin([self.vthr_dists[0][roc.number]-self.vthr_dists[step][roc.number] for step in range(1,5)])
            max_axis = numpy.amax([self.vthr_dists[0][roc.number]-self.vthr_dists[step][roc.number] for step in range(1,5)])
            vthr_stack = ROOT.THStack("%s_%s" %(self.dac, roc.number),"%s dist for each trim bit setting; %s; # pixels" %(self.dac, self.dac))
            for step in range(5):
                self._histos.append(plot.matrix_to_th2(self.vthr_dists[step][roc.number],'Vthr_Map_%s_ROC_%s' %(step, roc.number),'col','row'))
                if step == 0:
                    continue
                h_vthr = Plotter.create_th1(self.vthr_dists[0][roc.number]-self.vthr_dists[step][roc.number],'VthrCompDifference_Trim_%s_ROC_%s' %(self.trim_bit[step], roc.number), self.dac, '# pixels', min_axis, max_axis) 
                h_vthr.SetLineColor(color_dict[step])
                vthr_stack.Add(h_vthr)
                self._histos.append(h_vthr)
            self._histos.append(vthr_stack)
