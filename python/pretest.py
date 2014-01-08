import numpy
import Test

class Pretest(Test.Test):
    
    def prepare(self, config):
        self.dac1 = 'VthrComp'
        self.dac2 = 'CalDel'
        self.n_triggers = 10
        self._init_vthr = [roc.dac('VthrComp').value for roc in self.dut.rocs()]
        self._init_cal_del = [roc.dac('CalDel').value for roc in self.dut.rocs()]
        self._init_vsf = [roc.dac('Vsf').value for roc in self.dut.rocs()]
        self._init_vana = [roc.dac('Vana').value for roc in self.dut.rocs()]
        self.set_current_vana = 24.1
    
    def run(self, config):
        self.logger.info('Running pretest')
        self.rocs_programmable()
        self.adjust_vana()
        self.find_VthrComp_CalDel()
        self.adjust_PH_range()

    def cleanup(self, config):
        pass

    def rocs_programmable(self):
        '''Sets Vana to 0 and max DAC range and measures current, if difference is larger than 0.1 mA, ROC is programmable'''
        self.logger.info('Testing if ROCs are programmable')
        for roc in self.dut.rocs():
            self.tb.set_dac_roc(roc,'Vana', roc.dac('Vana').range-1)
            self.tb.m_delay(200)
            ia_on = self.tb.get_ia()
            self.tb.set_dac_roc(roc,'Vana', 0)
            self.tb.m_delay(200)
            ia_off = self.tb.get_ia()
            self.logger.debug('Vana = %s: ia = %.2f' %(roc.dac('Vana').range-1, ia_on))
            self.logger.debug('Vana = 0: ia = %.2f' %ia_off)
            if (ia_on-ia_off) > 0.1:
                self.logger.info('ROC %s is programmable' %roc.number)
            self.tb.set_dac_roc(roc, 'Vana', self._init_vana[roc.number])

    def adjust_vana(self):
        self.logger.info('Adjusting Vana')
        self.tb.set_dac('Vana', 0)
        self.tb.set_dac('Vsf', 0)
        zero_current = self.tb.get_ia()
        self.logger.info('Measured zero current ia = %.2f' %zero_current)
        self.tb.m_delay(200)
        set_current = zero_current
        for roc in self.dut.rocs():
            set_current += self.set_current_vana
            self.logger.info('Set current ia = %.2f' %set_current)
            low = 0
            high = roc.dac('Vana').range -1
            #Binary search to find value
            while low<high:
                vana = (high+low)//2
                self.tb.set_dac_roc(roc,'Vana', vana)
                self.tb.m_delay(200)
                ia = self.tb.get_ia()
                self.logger.debug('Ia = %.2f'%ia)
                if ia > set_current:
                    high = vana-1
                elif ia < set_current:
                    low = vana+1
                else:
                    break
            self.tb.set_dac_roc(roc, 'Vana', vana)
            self.tb.set_dac_roc(roc, 'Vsf', self._init_vsf[roc.number])
            self.logger.info('ROC %s found Vana: %s' %(roc.number, vana))

    def find_VthrComp_CalDel(self):
        #TODO remove hardcoding of 5,5
        return
        self.logger.info('Adjusting %s and %s' %(self.dac1, self.dac2))
        for roc in self.dut.rocs():
            roc.pixel(5,5).active = True
        self.tb.get_dac_dac(self.n_triggers, self.dac1, self.dac2)
        cal_dels = []
        vthr_comps = []
        for roc in self.dut.rocs():
            roc.pixel(5,5).active = False
            a_data = numpy.copy(roc.pixel(5,5).data)
            #Mask everything below half n_triggers as noise
            below_thresh = (a_data - self.n_triggers/2) < 0
            a_data = numpy.ma.masked_array(a_data, mask=below_thresh)
            #Sum over cal_del values, index is vthr_comp
            sum_on_vthr_comp = numpy.sum(a_data, axis=0)
            #Find noise cut as index with half the max sum
            noise_cut = numpy.amax(numpy.where(sum_on_vthr_comp > numpy.amax(sum_on_vthr_comp)/2))
            self.logger.debug('Found noise cutoff: %s = %s' %(self.dac1, noise_cut))
            #Set vthr_comp as half the noise
            vthr_comp = noise_cut/2
            vthr_comps.append(vthr_comp)
            #Find CalDel working point in half the working range
            cal_dels_fixed_vthr = numpy.where(a_data.T[vthr_comp] > self.n_triggers/2)
            cal_del = numpy.amin(cal_dels_fixed_vthr) + (numpy.amax(cal_dels_fixed_vthr)-numpy.amin(cal_dels_fixed_vthr))/2
            cal_dels.append(cal_del)
            self.tb.set_dac_roc(roc, self.dac1, vthr_comp)
            self.tb.set_dac_roc(roc, self.dac2, cal_del)
        self.logger.info('Found %s: %s and %s: %s' %(self.dac1, vthr_comps, self.dac2, cal_dels))

    def adjust_PH_range(self):
        #TODO implement
        pass
