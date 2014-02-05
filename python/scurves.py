import numpy
import test

class SCurves(test.Test):
    '''Write SCurveData (efficiency of Pixels for different Vcal values) for self.n_triggers scanning self.dac'''

    def prepare(self, config):
        self.n_triggers = int(config.get('SCurves','n_triggers'))
        self.dac = config.get('SCurves','dac')
        self.xtalk = 0
        self.reverse = False
        self.cals = 0
        self._scurve_data = [0]*256
        self.min_thr_dac = None
        self.max_thr_dac = None
        self.dut_thr_map = None
        self.scan_range = 32

    def dump_to_file(self):
        for roc in self.dut.rocs():
            outfile = open('%s/SCurveData_C%s.dat' %(self.directory, roc.number), 'w')
            outfile.write("Mode 1\n")
            for pixel in roc.pixels():
                rough_thr = self.dut_thr_map[roc.number][pixel.col][pixel.row]
                min_range = max(self.min_thr_dac, rough_thr-self.scan_range/2)
                max_range = min(self.max_thr_dac, rough_thr+self.scan_range/2)
                format_list = []
                for i in xrange(min_range, max_range):
                    format_list.append(self._scurve_data[i][roc.number][pixel.col][pixel.row])
                if not len(format_list) == self.scan_range:
                    self.logger.warning('No valid data for %s %s, filling 0' %(roc, pixel))
                    format_list = [0]*32
                outfile.write('%2.0f\t%3.0f\t'%(self.scan_range, rough_thr)+'\t'.join("%2.0f" % x for x in format_list)+'\n')
            outfile.close()    

    def run(self, config):
        #Measure map to determine rough threshold
        #TODO check if 4 is enough
        self.dut_thr_map = self.tb.get_threshold(4, self.dac, self.xtalk, self.cals, self.reverse)
        self.min_thr_dac = max(0, numpy.amin( numpy.ma.masked_less_equal(self.dut_thr_map,0) )-self.scan_range/2)
        self.max_thr_dac = min(255, numpy.amax( numpy.ma.masked_greater_equal(self.dut_thr_map,255) )+self.scan_range/2)
        #TODO remove and understand why threshold screws calibrate
        self.tb.init_dut(config)
        #Measure scan DAC around min and max threshold pm half the range
        self.logger.info('Scanning threshold in range %s < %s < %s' %(self.min_thr_dac, self.dac, self.max_thr_dac))
        for dac_value in xrange(self.min_thr_dac, self.max_thr_dac): 
            self.tb.set_dac(self.dac, dac_value)
            self.tb.get_calibrate(self.n_triggers)
            self._scurve_data[dac_value] = numpy.copy(self.dut.data)

    def dump(self):
        super(SCurves, self).dump()
        self.dump_to_file()
