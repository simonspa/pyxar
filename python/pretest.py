import numpy
import test

class Pretest(test.Test):
    
    def prepare(self, config):
        self.dac1 = 'VthrComp'
        self.dac2 = 'CalDel'
        self.n_triggers = 10
        self._init_vsf = [roc.dac('Vsf').value for roc in self.dut.rocs()]
        self._init_vana = [roc.dac('Vana').value for roc in self.dut.rocs()]
        self.roc_PH_map = []
        self.set_current_vana = 24.1
        self.minimal_diff = 1.
    
    def run(self, config):
        self.logger.info('Running pretest')
        self.rocs_programmable()
        self.adjust_vana()
        self.find_VthrComp_CalDel()
        self.adjust_PH_range()

    def cleanup(self, config):
        pass

    def restore(self):
        #Don't restore the default settings
        pass

    def rocs_programmable(self):
        '''Loops over all rocs and tests if ROC is programmable.
        Sets Vana to 0 and max DAC range and measures current, 
        if difference is larger than self.minimal_diff mA, ROC is programmable'''
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
            if (ia_on-ia_off) > self.minimal_diff:
                self.logger.info('ROC %s is programmable' %roc.number)
            self.tb.set_dac_roc(roc, 'Vana', self._init_vana[roc.number])

    def adjust_vana(self):
        '''Adjusts vana for all ROCs until ia = self.set_current_vana (24.1) mA'''
        self.logger.info('Adjusting Vana')
        #Turn of DUT
        self.tb.set_dac('Vana', 0)
        self.tb.set_dac('Vsf', 0)
        self.tb.m_delay(200)
        #Measure zero current using three measurements
        zero_current = 0
        n_meas = 3
        for i in range(n_meas):
            zero_current += self.tb.get_ia()
            self.tb.m_delay(200)
        zero_current /= float(n_meas)
        self.logger.info('Measured zero current ia = %.2f' %zero_current)
        set_current = zero_current
        #Loop over ROCs and adjust vana
        for roc in self.dut.rocs():
            set_current += self.set_current_vana
            self.logger.info('Set current ia = %.2f' %set_current)
            #Binary search in vana until self.tb.get_ia() = set_current
            vana = self.tb.binary_search(roc, 'Vana', set_current, lambda: self.tb.get_ia() )
            self.tb.set_dac_roc(roc, 'Vana', vana)
            self.tb.set_dac_roc(roc, 'Vsf', self._init_vsf[roc.number])
            self.logger.info('ROC %s found Vana: %s' %(roc.number, vana))

    def find_VthrComp_CalDel(self):
        '''Perform a DacDac scan in VthrComp and CalDel to find a working point.
        VthrComp is adjusted to half the noise cutoff. 
        CalDel is centered in the working range.'''
        #TODO remove hardcoding of 5,5
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
        #TODO complete
        self.logger.info('Adjusting PH DACs')

        ph_max = 255
        ph_min = 0
        stepwidth = 5
        safety_margin = 10
        ADC_max = 255
        self.n_triggers = 1
        self.dac = 'Vcal'
        self.xtalk = 0
        self.cals = 0
        self.reverse = False

        self.roc_Vcal_map = self.tb.get_threshold(5, self.dac, self.xtalk, self.cals, self.reverse)
        #loop over ROCs to adjust VIref_ADC and VoffsetRO for each ROC  
        for roc in self.dut.rocs():
            #measure Vcal map to determine minimal Vcal for which all pixels respond
            Vcal_min = numpy.amax(numpy.ma.masked_greater_equal(self.roc_Vcal_map[roc.number],256))
            self.logger.info('Minimal Vcal required for all pixels to respond is %s' %(Vcal_min))
            #make sure that no pixel has PH outside dynamic range of the ADC
            self.logger.info('Limiting PH to dynamic range of ADC for %s' %(roc))
            #check upper edge of ADC range
            self.tb.set_dac_roc(roc, 'Vcal', 255)
            self.tb.set_dac_roc(roc, 'CtrlReg', 4)
            #Measure PH map to find pixel with highest PH
            self.tb.get_ph_roc(self.n_triggers, roc)
            self.roc_PH_map = roc.data
            ph_max = numpy.amax(numpy.ma.masked_greater_equal(self.roc_PH_map,256))
            self.logger.debug('ph_max = %s' %(ph_max))
            col,row =  numpy.unravel_index(numpy.argmax(numpy.ma.masked_greater(self.roc_PH_map,ph_max)),numpy.shape(self.roc_PH_map))
            self.logger.debug('Pixel with highest PH for Vcal 255 high range: %s,%s' %(col, row))
            #Set and print start value of VIref_ADC
            viref_adc = roc.dac('VIref_ADC').value
            self.logger.info('Original  VIref_ADC = %s' %(viref_adc))
            #Reduce PH of all pixels to upper limit of ADC range by increasing VIref_ADC
            while ph_max > (ADC_max - safety_margin):
                if viref_adc + stepwidth > 255:
                    self.logger.warning('Cannot increase VIref_ADC to compress PH range')
                    break #TODO: implement smoother exception handling
                else:
                    viref_adc += stepwidth
                    self.tb.set_dac_roc(roc, 'VIref_ADC', viref_adc)
                    self.logger.debug('Increased VIref_ADC to %s, to compress PH range (at upper edge' %(viref_adc))
                    self.tb.get_ph_roc(self.n_triggers, roc)
                    self.roc_PH_map = roc.data
                    ph_max = numpy.amax(numpy.ma.masked_greater_equal(self.roc_PH_map,256))
                    self.logger.debug('ph_max = %s' %(ph_max))
                    col,row =  numpy.unravel_index(numpy.argmax(numpy.ma.masked_greater(self.roc_PH_map,ph_max)),numpy.shape(self.roc_PH_map))
            self.logger.debug('Pixel with highest PH for Vcal 255 high range: %s,%s' %(col, row))
            
            #Reduce PH of all pixels to lower limit of ADC range by increasing VIref_ADC, use Vcal_min found in Vcal map ti make sure all (untrimmed) pixels respond
            self.tb.set_dac_roc(roc, 'Vcal', Vcal_min)
            self.tb.set_dac_roc(roc, 'CtrlReg', 0)
            self.tb.get_ph_roc(self.n_triggers, roc)
            self.roc_PH_map = roc.data
            ph_min = numpy.amin(numpy.ma.masked_less_equal(self.roc_PH_map,0))
            self.logger.debug('ph_min = %s' %(ph_min))
            col_min,row_min =  numpy.unravel_index(numpy.argmax(numpy.ma.masked_greater(self.roc_PH_map,ph_min)),numpy.shape(self.roc_PH_map))
            self.logger.debug('Pixel with lowest PH for low Vcal: %s,%s' %(col_min, row_min))
            while ph_min < safety_margin:
                if roc.dac('VIref_ADC').value + stepwidth > 255:
                    self.logger.warning('Cannot increase VIref_ADC to compress PH range')
                    break #TODO: implement smoother exception handling
                else:           
                    viref_adc = roc.dac('VIref_ADC').value + stepwidth
                    self.tb.set_dac_roc(roc, 'VIref_ADC', viref_adc)
                    self.logger.debug('Increased %s, to compress PH range (at lower edge)' %(viref_adc))
                    self.tb.get_ph_roc(self.n_triggers, roc)
                    self.roc_PH_map = roc.data
                    ph_min= numpy.amin(numpy.ma.masked_less_equal(self.roc_PH_map,0))
                    self.logger.debug('ph_min = %s' %(ph_min))
                    col_min,row_min =  numpy.unravel_index(numpy.argmax(numpy.ma.masked_greater(self.roc_PH_map,ph_min)),numpy.shape(self.roc_PH_map))
            self.logger.debug('Pixel with lowest PH for small Vcal: %s,%s' %(col_min, row_min))
            self.logger.info('VIref_ADC after compressing PH: %s' %(viref_adc))
        

            #Center PH in ADC range
            self.logger.info('Centering PH in ADC range for %s' %(roc))
            #Calculate margin between highest PH and upper edge of ADC range            
            self.tb.set_dac_roc(roc, 'CtrlReg', 4)
            pixel_high = roc.pixel(col, row)
            pixel_low = roc.pixel(col_min, row_min)
            pixel_high.active = True
            self.tb.get_ph_dac(self.n_triggers, 'Vcal')
            ph_max = numpy.amax(numpy.ma.masked_greater_equal(pixel_high.data,256))
            self.logger.debug('ph_max for pixel_high = %s' %(ph_max))
            pixel_high.active = False
            upper_margin = ADC_max - ph_max
            self.logger.debug('upper_margin: %s' %(upper_margin))
            #Calculate margin between lowest PH and lower edge of ADC range            
            pixel_low.active = True
            self.tb.set_dac_roc(roc, 'CtrlReg', 0)
            self.tb.get_ph_dac(self.n_triggers, 'Vcal')
            ph_min = numpy.amin(numpy.ma.masked_less_equal(pixel_low.data,0))
            self.logger.debug('ph_min for pixel_low = %s' %(ph_min))  
            lower_margin = ph_min
            self.logger.debug('lower_margin: %s' %(lower_margin))
            pixel_low.active = False
            pixel_high.active= True
            self.tb.set_dac_roc(roc, 'CtrlReg', 4)
            #Determine target margin for centered PH
            z = 0.5 * (upper_margin + lower_margin)
            self.logger.debug('z = %s' %(z))
            voffsetro = roc.dac('VOffsetR0').value
            #Adjust VOffsetRO to center PH in ADC range
            #If PH is to high, shift downwards (increase VOffsetRO)
            while upper_margin < z-5 and voffsetro <= 255-stepwidth:
                voffsetro += stepwidth
                self.tb.set_dac_roc(roc, 'VOffsetR0', voffsetro)
                self.logger.debug('Increased VOffsetRO to %s, to center PH' %(voffsetro))
                self.tb.get_ph_dac(self.n_triggers, 'Vcal')
                ph_max = numpy.amax(numpy.ma.masked_greater_equal(pixel_high.data,256))
                upper_margin = ADC_max - ph_max
                self.logger.debug('upper_margin = %s' %(upper_margin))
            #If PH is to low, shift upwards (decrease VOffsetRO)
            while upper_margin > z+5 and voffsetro >= stepwidth:
                voffsetro -= stepwidth
                self.tb.set_dac_roc(roc, 'VOffsetR0', voffsetro)
                self.logger.debug('Decreased VoffsetRO to %s, to center PH' %(voffsetro))
                self.tb.get_ph_dac(self.n_triggers, 'Vcal')
                ph_max = numpy.amax(numpy.ma.masked_greater_equal(pixel_high.data,256))
                upper_margin = ADC_max - ph_max
                self.logger.debug('upper_margin = %s' %(upper_margin))
            self.logger.info('VoffsetRO after centering PH for selected pixel: %s' %(voffsetro))
            pixel_high.active = False
            #Measure minimal PH after centering (maximal PH already measured)
            pixel_low.active= True
            self.tb.set_dac_roc(roc, 'CtrlReg', 0)
            self.tb.get_ph_dac(self.n_triggers, 'Vcal')
            ph_min = numpy.amin(numpy.ma.masked_less_equal(pixel_low.data,0))
            self.logger.debug('ph_min for pixel_low = %s' %(ph_min))
            self.logger.debug('ph_max for pixel_high = %s' %(ph_max))
            pixel_low.active = False 
            
            #Stretch PH over full ADC range by decreasing VIref_ADC (using pixel with highest PH)
            pixel_high.active = True
            self.logger.info('Stretching PH over full ADC range for ROC %s' %(roc))
            while ph_max < (ADC_max - safety_margin):
                self.tb.set_dac_roc(roc, 'CtrlReg', 4)
                viref_adc = roc.dac('VIref_ADC').value - stepwidth
                self.tb.set_dac_roc(roc, 'VIref_ADC', viref_adc)
                self.tb.get_ph_dac(self.n_triggers, 'Vcal')
                ph_max = numpy.amax(numpy.ma.masked_greater_equal(pixel_high.data,256))
                self.logger.debug('Decreased VIref_ADC to %s, to stretch PH over full ADC range' %(voffsetro))
                self.logger.debug('ph_max for selected pixel= %s' %(ph_max))  
            pixel_high.active = False
            
            #Set control register back to low range 
            self.tb.set_dac_roc(roc, 'CtrlReg', roc.dac('CtrlReg').stored_value)
            self.tb.set_dac_roc(roc, 'Vcal', roc.dac('Vcal').stored_value)
            #Print out optimized PH Dacs
            self.logger.info('++++++++++++++++++++++++++++++++++++++++++')
            self.logger.info('Found VIref_ADC = %s and VOffsetRO = %s for %s' %(viref_adc, voffsetro, roc))



