import dtb
import logging
import numpy
from helpers import list_to_matrix

class Testboard(dtb.PyDTB):
    
    def __init__(self, config, dut):
        super(Testboard, self).__init__()
        self.dut = dut
        usb_id = config.get('Testboard','id')
        self.logger = logging.getLogger(__name__)
        self.logger.info('Using testboard id: %s' %usb_id)
        self.open(usb_id)
        self._set_max_vals(config)
        #TODO expose timing to config
        self.set_mhz(0)
        self.init_pg()
        #END TODO
        self.pon()
        if eval(config.get('Testboard','hv_on')):
            self.hv_on()
        self.init_dut(config)

    def _set_max_vals(self, config):
        max_ia = int(config.get('Testboard','max_ia'))
        max_id = int(config.get('Testboard','max_id'))
        max_va = int(config.get('Testboard','max_va'))
        max_vd = int(config.get('Testboard','max_vd'))
        self.logger.info('Max IA: %s' %max_ia)
        self.set_ia(max_ia)
        self.logger.info('Max ID: %s' %max_id)
        self.set_id(max_id)
        self.logger.info('Max VA: %s' %max_va)
        self.set_va(max_va)
        self.logger.info('Max VD: %s' %max_vd)
        self.set_vd(max_vd)

    def __del__(self):
        self.logger.info("Deleting testboard")
        self.hv_off()
        self.poff()
        self.cleanup()

    def init_tbm(self, tbm):
        self.logger.info('Initializing %s' %tbm)
        self.flush()

    def set_dacs(self, roc):
        self.flush()
        self.logger.debug('Setting DACs of %s' %roc)
        for dac in roc.dacs():
            self.logger.debug('Setting dac: %s' %dac)
            self.roc_set_DAC(dac.number, dac.value)
        self.flush()
    
    def set_dac(self, reg, value):
        self.flush()
        for roc in self.dut.rocs():
            self.select_roc(roc)
            roc.dac(reg).value = value
            self.logger.debug('Setting %s %s' %(roc, roc.dac(reg)))
            self.roc_set_DAC(roc.dac(reg).number, roc.dac(reg).value)

    def select_roc(self, roc):
        #TODO check if roc is already active
        self.i2_c_addr(roc.number)
        self.set_roc_addr(roc.number)
        #TODO move delay to FW
        self.m_delay(200)

    def init_roc(self, roc):
        self.logger.info('Initializing ROC: %s' %roc.number)
        self.select_roc(roc)
        self.set_dacs(roc)
        self.logger.debug('Applying trimming to ROC: %s' %roc)
        #TODO check that the translation to TB is really correct
        self.trim_chip(roc.trim_for_tb)
        self.roc_clr_cal()
        self.flush()

    def init_dut(self, config):
        for roc in self.dut.rocs():
            self.init_roc(roc)
    
    def trim(self, trim_bits):
        self.dut.trim = trim_bits
        for roc in self.dut.rocs():
            #TODO check that the translation to TB is really correct
            self.trim_chip(roc.trim_for_tb)

    def get_calibrate(self, n_triggers):
        for roc in self.dut.rocs():
            self.select_roc(roc)
            n_hits = []
            ph_sum = []
            self.calibrate(n_triggers, n_hits, ph_sum)
            self.set_dacs(roc)
            roc.data = list_to_matrix(roc.n_cols, roc.n_rows, ph_sum)

    def get_dac_dac(self, n_triggers, dac1, dac2):
        for roc in self.dut.rocs():
            self.select_roc(roc)
            #TODO TB function has too long vector by one unit
            dac_range1 = roc.dac(dac1).range-1
            dac_range2 = roc.dac(dac2).range-1
            n_results = dac_range1*dac_range2
            for pixel in roc.active_pixels():
                n_hits = []
                ph_sum = []
                self.logger.debug('DacDac pix(%s,%s), nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac1, dac_range1, dac2, dac_range2) )
                self.dac_dac(n_triggers, pixel.col, pixel.row, roc.dac(dac1).number, dac_range1, roc.dac(dac2).number, dac_range2, n_hits, ph_sum)
                self.set_dacs(roc)
                pixel.data = numpy.transpose(list_to_matrix(dac_range1, dac_range2, n_hits))

    def get_threshold(self, n_triggers, dac, xtalk, cals, reverse):
        #TODO Don't hardcode pars, they will go away with new CTestboard
        start = 0
        step = 1
        if reverse: 
            step = -1
        thr_level = int(n_triggers/2.)
        for roc in self.dut.rocs():
            self.select_roc(roc)
            self.logger.info('Start: %s, step: %s, thr_level: %s, n_triggers: %s, dac: %s, xtalk: %s, cals: %s' %(start, step, thr_level, n_triggers, dac, xtalk, cals))
            result = [0] * roc.n_pixels
            #TODO remove trimming, they will go away with new CTestboard
            trim = roc.trim_for_tb 
            self.chip_threshold(start, step, thr_level, n_triggers, roc.dac(dac).number , xtalk, cals, trim, result)
            self.set_dacs(roc)
            roc.data = list_to_matrix(roc.n_cols, roc.n_rows, result)
        return self.dut.roc_data
            
    def arm(self, pixel):
        if not pixel.mask:
            self.arm_pixel(pixel.col, pixel.row)
    
    def disarm(self, pixel):
        self.disarm_pixel(pixel.col, pixel.row)
    
    def ia(self):
        self.logger.info('IA: %.2f mA' %self.get_ia())
    
    def id(self):
        self.logger.info('ID: %.2f mA' %self.get_id())
