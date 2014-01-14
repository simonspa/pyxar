import test
import numpy
import ROOT
from plotter import Plotter

class Trim(test.Test):

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
        for i,roc in enumerate(self.dut.rocs()):
            self.tb.set_dac_roc(roc,'VthrComp', self.vthr[i])
        #Determine min vtrim
        self.get_vtrim()
        for i,roc in enumerate(self.dut.rocs()):
            self.tb.set_dac_roc(roc,'Vtrim', self.vtrim[i])
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
        color_dict = [1,13,15,17,2]
        #TODO decide what is important to the user
        plot = Plotter(self.config, self)
        for roc in self.dut.rocs():
            #save data
            roc.save(self.vcal)
            min_axis = numpy.amin(self.vcal_dists)
            max_axis = numpy.amax(self.vcal_dists)
            vcal_stack = ROOT.THStack("Vcal %s" %roc.number,"Vcal dist for each trimming step; Vcal; # pixels")
            trim_stack = ROOT.THStack("TrimBits %s" %roc.number,"Trim bits for each trimming step; TrimBit; # pixels")
            try:
                self._histos.append(plot.matrix_to_th2(self.dut_VthrComp_map[roc.number],'Vthr_Map_ROC_%s'%roc.number,'col','row'))
                self._histos.append(plot.matrix_to_th2(self.dut_Noise_map[roc.number],'Noise_Map_ROC_%s'%roc.number,'col','row'))
            except AttributeError:
                pass
            for step in range(self.n_steps+1):
                self._histos.append(plot.matrix_to_th2(self.vcal_dists[step][roc.number],'Vcal_Map_%s_ROC_%s' %(step, roc.number),'col','row'))
                h_vcal = Plotter.create_th1(self.vcal_dists[step][roc.number],'%s_ROC_%s' %(step, roc.number), self.dac, '# pixels', min_axis, max_axis) 
                h_vcal.SetLineColor(color_dict[step])
                vcal_stack.Add(h_vcal)
                h_trim = Plotter.create_th1(self.trim_dists[step][roc.number],'%s_ROC_%s' %(step, roc.number), 'Trim bit', '# pixels', self._min_trim_bit, self._max_trim_bit) 
                h_trim.SetLineColor(color_dict[step])
                if step == 4:
                    h_trim.SetFillStyle(3002)
                    h_trim.SetFillColor(color_dict[step])
                    h_vcal.SetFillStyle(3002)
                    h_vcal.SetFillColor(color_dict[step])
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
            thr = self.vthr
            self.vthr = []
            for roc in self.dut.rocs():
                self.vthr.append(thr)
            self.logger.info('Using min VthrComp %s from config' %self.vthr)
            return
        #Set vcal to expected value
        self.tb.set_dac('Vcal', self.vcal)
        #self.tb.flush()
        #TODO check if cals=False makes sense
        self.dut_VthrComp_map = self.tb.get_threshold(self.n_triggers, 'VthrComp', self.xtalk, self.cals, self.reverse)
        self.dut_Noise_map = self.tb.get_threshold(self.n_triggers, 'VthrComp', self.xtalk, self.cals, True)
        #TODO think of data structure for DUT
        self.vthr = []
        for roc in self.dut.rocs():
            dut_vthr_min = numpy.amin(self.dut_VthrComp_map[roc.number])
            dut_noise_min = numpy.amin(self.dut_Noise_map[roc.number])
            #todo self.vthr...?
            if dut_vthr_min < dut_noise_min -10:
                dut_vthr_min = dut_noise_min -10
            self.vthr.append(dut_vthr_min)
            #self.tb.set_dac_roc(roc,'VthrComp', dut_vthr_min)
            #self.logger.info('Determined VthrComp %s for %s' %(self.vthr,roc))
        #TODO remove hardcoded values
        self.tb.set_dac('Vcal', 200)

    def get_vtrim(self):
        if self.vtrim > 0:
            vtrim = self.vtrim
            self.vtrim = []
            for roc in self.dut.rocs():
                self.vtrim.append(vtrim)
            self.logger.info('Using min Vtrim %s from config' %self.vtrim)
            return
        else:
            #TODO implement pixel threshold
            #get Vcal Map
            dut_Vcal_map = self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse)
            #ToDo
            #self.tb.daq_enable()
            self.vtrim = []
            for roc in self.dut.rocs():
                #determine limit 5 standard deviations away from mean or 254 
                vcalMaxLimit = min(254,numpy.mean(dut_Vcal_map[roc.number])+5*numpy.std(dut_Vcal_map[roc.number]))
                #get maximum Vcal pixel
                col,row =  numpy.unravel_index(numpy.argmax(numpy.ma.masked_greater(dut_Vcal_map[roc.number],vcalMaxLimit)),numpy.shape(dut_Vcal_map[roc.number]))
                self.logger.info('Maximum Vcal of %s in Pixel %s, %s in %s'%(dut_Vcal_map[roc.number,col,row],col,row,roc))
                vtrim = 0
                self.tb.select_roc(roc)
                self.tb.arm_pixel(col,row)
                found = False
                low =0
                high=255
                while low<high:
                    vtrim = (high+low)//2
                    self.tb.set_dac_roc(roc,'Vtrim', vtrim)
                    thr = self.tb.pixel_threshold(self.n_triggers, col, row, 0, 1, self.n_triggers/2, 25, False, False, 0)
                    self.logger.debug('threshold = %s'%thr)
                    if thr < self.vcal:
                        high = vtrim-1
                    elif thr > self.vcal:
                        low = vtrim+1
                    else:
                        break

                #while vtrim<255:
                #    self.tb.set_dac_roc(roc,'Vtrim', vtrim)
                #    thr = self.tb.pixel_threshold(self.n_triggers, col, row, 0, 1, self.n_triggers/2, 25, False, False, 0)
                #    self.logger.debug('threshold = %s'%thr)
                #    if  thr < self.vcal:
                #        break
                #    vtrim+=1
                #self.tb.daq_disable()
                self.tb.disarm_pixel(col,row)
                #TODO determine necessary Vtrim for this pixel
                self.logger.info('Found Vtrim %s'%vtrim)
                #TODO self.vtrim
                self.vtrim.append(vtrim)
                self.logger.info('Determined Vtrim %s' %self.vtrim)

