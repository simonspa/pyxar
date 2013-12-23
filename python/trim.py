import Test
import numpy
import ROOT
from plotter import Plotter

class Trim(Test.Test):

    def prepare(self, config):
        self.vcal = int(config.get('Trim','Vcal'))
        self.vtrim = int(config.get('Trim','Vtrim'))
        self.vthr = int(config.get('Trim','VthrComp'))
        self.cals = 0
        self.xtalk = 0
        self.dac = 'Vcal'
        self.n_triggers = int(config.get('Trim','n_triggers'))
        self.reverse = False
        self.n_steps = 4
        self._min_trim_bit = 0
        self._max_trim_bit = 15
        self.vcal_dists = []
        self.trim_dists = []

    def run(self, config): 
        pass
        self.logger.info('Running trimming to Vcal %s' %self.vcal)
        #Determine min vthr
        self.get_vthr()
        self.tb.set_dac('VthrComp', self.vthr)
        #Determine min vtrim
        self.get_vtrim()
        self.tb.set_dac('Vtrim', self.vtrim)
        #Get trim bits and set them to half the max range
        trim_bits = self.dut.trim
        numpy.clip(trim_bits, self._max_trim_bit/2, self._max_trim_bit/2, out=trim_bits)
        self.tb.trim(trim_bits)
        self.trim_dists.append(trim_bits)
        #Measure initial DUT with trim bits 7
        self.vcal_dists.append(self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse))
        #Run binary search
        for step in range(self.n_steps):
            self.trim_step(step)

    def cleanup(self, config):
        #TODO decide what is important to the user
        plot = Plotter(self.config, self)
        for roc in self.dut.rocs():
            min_axis = numpy.amin(self.vcal_dists)
            max_axis = numpy.amax(self.vcal_dists)
            vcal_stack = ROOT.THStack("Trim %s" %roc.number,"Vcal dist for each trimming step")
            trim_stack = ROOT.THStack("Vcal %s" %roc.number,"Trim bits for each trimming step")
            for step in range(self.n_steps+1):
                h_vcal = Plotter.create_th1(self.vcal_dists[step][roc.number],'%s_ROC_%s' %(step, roc.number), self.dac, '# pixels', min_axis, max_axis) 
                h_vcal.SetLineColor(step+1)
                vcal_stack.Add(h_vcal)
                h_trim = Plotter.create_th1(self.trim_dists[step][roc.number],'%s_ROC_%s' %(step, roc.number), 'Trim bit', '# pixels', self._min_trim_bit, self._max_trim_bit) 
                h_trim.SetLineColor(step+1)
                trim_stack.Add(h_trim)
            self._histos.append(trim_stack)
            self._histos.append(vcal_stack)

    def trim_correction(self, step, orig_trim, trim_high):
        #If larger apply trim lower, else trim higher
        correction = self.n_steps - step
        trim_bits = numpy.copy(orig_trim)
        #Mask all entries to be trimmed higher
        new_trim = numpy.ma.masked_array(trim_bits, mask=trim_high)
        new_trim -= correction 
        #Mask all entries to be trimmed lower
        new_trim.mask = numpy.invert(trim_high)
        new_trim += correction 
        #Unmask all
        new_trim.mask = False
        low_val = new_trim < self._min_trim_bit  # Where values are too low
        new_trim[low_val] = self._min_trim_bit
        high_val = new_trim > self._max_trim_bit  # Where values are too high
        new_trim[high_val] = self._max_trim_bit
        return numpy.copy(new_trim)

    def trim_step(self, step):
        self.logger.info('Running trim step %s / 4' %(1+step))
        self.logger.debug('Trim of ROC0 Pix(0,2) %s VcalThr %s' %(self.dut.pixel(0,0,2).trim, self.vcal_dists[step][0][0][2]))
        #Get trim bits from DUT
        orig_trim = self.dut.trim
        #Compare to Vcal from first map, if larger trim lower, else trim higher
        #Get all DUT pixels to be trimmed higher
        trim_high = ((self.vcal_dists[step] - self.vcal) < 0)
        new_trim = self.trim_correction(step, orig_trim, trim_high)
        #Trim DUT using new corrections
        self.tb.trim(new_trim)
        #Measure trimmed DUT
        self.vcal_dists.append(self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse))
        self.logger.debug('Trim of ROC0 Pix(0,2) %s VcalThr %s' %(self.dut.pixel(0,0,2).trim, self.vcal_dists[step+1][0][0][2]))
        #If new distribution is closer to vcal, keep trim bit, else discard
        not_trim = (abs(self.vcal_dists[step+1] - self.vcal) > abs(self.vcal_dists[step] - self.vcal))
        # reset the trim bits accordingly
        new_trim = numpy.ma.masked_array(new_trim, mask=numpy.invert(not_trim))
        new_trim += orig_trim - new_trim #setting new trim to orig
        new_trim.mask = False
        self.tb.trim(new_trim)
        self.trim_dists.append(new_trim)
        # reset the map accordingly,
        self.vcal_dists[step+1] = numpy.ma.masked_array(self.vcal_dists[step+1], mask=numpy.invert(not_trim))
        self.vcal_dists[step+1] += self.vcal_dists[step] - self.vcal_dists[step+1] #setting new vcal map to map of step before
        self.vcal_dists[step+1].mask = False
        self.logger.debug('Trim of ROC0 Pix(0,2) %s VcalThr %s' %(self.dut.pixel(0,0,2).trim, self.vcal_dists[step+1][0][0][2]))
    
    def get_vthr(self):
        if self.vthr > 0:
            self.logger.info('Using min VthrComp %s from config' %self.vthr)
            return
        #Set vcal to expected value
        self.tb.set_dac('Vcal', self.vcal)
        #TODO check if cals=False makes sense
        dut_VthrComp_map = self.tb.get_threshold(self.n_triggers, 'VthrComp', self.xtalk, self.cals, self.reverse)
        #TODO think of data structure for DUT
        dut_vthr_min = numpy.amin(dut_VthrComp_map) 
        self.vthr = dut_vthr_min
        self.tb.set_dac('VthrComp', self.vthr)
        #TODO remove hardcoded values
        self.tb.set_dac('Vcal', 200)
        self.logger.info('Determined VthrComp %s' %self.vthr)

    def get_vtrim(self):
        if self.vtrim > 0:
            self.logger.info('Using min Vtrim %s from config' %self.vtrim)
            return
        #TODO implement pixel threshold
        dut_Vcal_map = self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse)
        self.logger.info('Determined Vtrim %s' %self.vtrim)
