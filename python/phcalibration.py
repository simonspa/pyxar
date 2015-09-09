import numpy
import test

class PHCalibration(test.Test):
    ''' get average pulsheight for n triggers at several Vcal values and write to file '''

    def prepare(self, config):
        self.n_triggers = int(config.get('PHCalibration','n_triggers'))
        self.points_lowrange = config.get('PHCalibration','points_lowrange').split(',')
        self.points_highrange = config.get('PHCalibration','points_highrange').split(',')
        self.dac = 'Vcal'
        self.xtalk = 0
        self.reverse = False
        self.cals = 0
        self._ph_data = []

    def dump_to_file(self):
        for i, roc in enumerate(self.dut.rocs()):
            outfile = open('%s/phCalibration_C%s.dat' %(self.directory, roc.number), 'w')
            outfile.write('Pulse heights for the following Vcal values:\n')
            outfile.write('Low range: %s\n'%' '.join(self.points_lowrange))
            outfile.write('High range: %s\n\n'%' '.join(self.points_highrange))
            for pixel in roc.pixels():
                format_list = []
                for point in self._ph_data:
                    format_list.append(point[i][pixel.col][pixel.row])
                outfile.write("\t".join("%2.0f" % x for x in format_list)+'\tPix %i %i'%(pixel.col,pixel.row)+"\n")
            outfile.close()

    def run(self, config):
        self.tb.m_delay(1000)
        #Measure scan DAC around min and max threshold pm half the range
        self.tb.set_dac('CtrlReg',0)
        for point in self.points_lowrange:
            self.logger.info('Scanning Pulseheight for Vcal %s (lowrange)'%point)
            self.get_point(point)
        self.tb.set_dac('CtrlReg',4)
        for point in self.points_highrange:
            self.logger.info('Scanning Pulseheight for Vcal %s (highrange)'%point)
            self.get_point(point)

    def get_point(self, point):
        self.tb.set_dac(self.dac, int(point))
        self.tb.get_ph(self.n_triggers)
        self._ph_data.append(numpy.copy(self.dut.data))

    def dump(self):
        super(PHCalibration, self).dump()
        self.dump_to_file()
