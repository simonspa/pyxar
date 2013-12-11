import dtb
import logging

class Testboard(dtb.PyDTB):
    
    def __init__(self, config, dut):
        super(Testboard, self).__init__()
        self.dut = dut
        usb_id = config.get('Testboard','id')
        self.logger = logging.getLogger(__name__)
        self.logger.info('Using testboard id: %s' %usb_id)
        self.find_dtb(usb_id)
        self.open(usb_id)
        self.pon()
        self.i2_c_addr(0);
        self.prep_dig_test()
        self.set_ia(1199);
        self.set_id(1000);
        self.set_va(1699);
        self.set_vd(2500);
        self.hv_on()
        self.reset_on()
        self.reset_off()
        self.init_roc()
        self.flush()

    def __del__(self):
        self.logger.info("Deleting Testboard")
        self.hv_off();
        self.poff();
        self.cleanup();

