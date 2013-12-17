import dtb
import logging

class Testboard(dtb.PyDTB):
    
    def __init__(self, config, dut):
        super(Testboard, self).__init__()
        self.dut = dut
        usb_id = config.get('Testboard','id')
        self.logger = logging.getLogger(__name__)
        self.logger.info('Using testboard id: %s' %usb_id)
        self.open(usb_id)
        self.pon()
        #TODO expose timing to config
        self.set_mhz(0)
        self.init_pg()
        #END TODO
        self.set_ia(int(config.get('Testboard','max_ia')))
        self.set_id(int(config.get('Testboard','max_id')))
        self.set_va(int(config.get('Testboard','max_va')))
        self.set_vd(int(config.get('Testboard','max_vd')))
        if eval(config.get('Testboard','hv_on')):
            self.hv_on()
        self.reset_on()
        self.reset_off()
        self.flush()
        self.init_dut(config)

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
        self.logger.info('Initializing TBM: %s' %roc)
        self.i2_c_addr(roc.number);
        for dac in roc.dacs():
            self.logger.debug('Setting dac: %s' %dac)
            self.roc_set_DAC(dac.number, dac.value)
        self.roc_chip_mask()
        self.flush()

    def init_dut(self, config):
        for roc in self.dut.rocs():
            self.init_roc(roc)
            
    def arm(self, pixel):
        if not pixel.mask:
            self.arm_pixel(pixel.col, pixel.row)
    
    def disarm(self, pixel):
        self.disarm_pixel(pixel.col, pixel.row)
