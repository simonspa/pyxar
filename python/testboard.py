import dtb
import logging
from helpers import list_to_grid

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
        self.logger.debug('Max IA: %s' %max_ia)
        self.set_ia(max_ia)
        self.logger.debug('Max ID: %s' %max_id)
        self.set_id(max_id)
        self.logger.debug('Max VA: %s' %max_va)
        self.set_va(max_va)
        self.logger.debug('Max VD: %s' %max_vd)
        self.set_vd(max_vd)

    def __del__(self):
        self.logger.info("Deleting testboard")
        self.hv_off()
        self.poff()
        self.cleanup()

    def init_tbm(self, tbm):
        self.logger.info('Initializing TBM: %s' %tbm)
        self.flush()
        pass

    def init_roc(self, roc):
        self.logger.info('Initializing ROC: %s' %roc.number)
        self.i2_c_addr(roc.number)
        self.set_roc_addr(roc.number)
        #TODO move delay to FW
        self.m_delay(200)
        for dac in roc.dacs():
            self.logger.debug('Setting dac: %s' %dac)
            self.roc_set_DAC(dac.number, dac.value)
        self.flush()
        self.logger.debug('Trimming ROC: %s' %roc)
        trim = [15] * 4160
        self.trim(trim)
        self.flush()

    def init_dut(self, config):
        for roc in self.dut.rocs():
            self.init_roc(roc)

    def get_calibrate(self, n_triggers):
        for roc in self.dut.rocs():
            n_hits = []
            ph_sum = []
            self.calibrate(n_triggers, n_hits, ph_sum)
            #TODO adapt DUT datastructure
            self.init_roc(roc)
            return list_to_grid(roc.n_rows, roc.n_cols, ph_sum)

    def get_dac_dac(self, n_triggers, dac1, dac2):
        for roc in self.dut.rocs():
            #TODO TB function has too long vector by one unit
            dac_range1 = roc.dac(dac1).range-1
            dac_range2 = roc.dac(dac2).range-1
            n_results = dac_range1*dac_range2
            for pixel in roc.active_pixels():
                n_hits = []
                ph_sum = []
                self.logger.debug('DacDac pix(%s,%s), nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac1, dac_range1, dac2, dac_range2) )
                #TODO TB function has too long vector by one unit
                self.dac_dac(n_triggers, pixel.col, pixel.row, dac1, dac_range1, dac2, dac_range2, n_hits, ph_sum)
                #TODO adapt DUT datastructure
                self.init_roc(roc)
                return list_to_grid(dac_range1, dac_range2, n_hits)
            
    def arm(self, pixel):
        if not pixel.mask:
            self.arm_pixel(pixel.col, pixel.row)
    
    def disarm(self, pixel):
        self.disarm_pixel(pixel.col, pixel.row)
    
    def ia(self):
        self.logger.info('IA: %.2f mA' %self.get_ia())
    
    def id(self):
        self.logger.info('ID: %.2f mA' %self.get_id())
