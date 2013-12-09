from dtb import PyDTB
from helpers import list_to_grid

class Testboard(object):
    
    def __init__(self, config):
        #usb_id = "DTB_WRMU7H"
        usb_id = "DTB_WRQ4OZ"
        print usb_id
        self.tb = PyDTB()
        self.tb.find_dtb(usb_id)
        self.tb.open(usb_id)
        self.tb.pon()
        self.tb.i2_c_addr(0);
        self.tb.prep_dig_test()
        self.tb.set_ia(1199);
        self.tb.set_id(1000);
        self.tb.set_va(1699);
        self.tb.set_vd(2500);
        self.tb.hv_on()
        self.tb.reset_on()
        self.tb.reset_off()
        self.tb.init_roc()
        self.tb.flush()



    def __del__(self):
        print "Del TB!"
        self.tb.hv_off();
        self.tb.poff();
        self.tb.cleanup();

    def transform_result(func):
        """Decorator to transform the list output into a grid using list to grid"""
        def wrapper(*args):
            return list_to_grid(args[1].n_rows, args[1].n_cols, func(*args))
        return wrapper

    @transform_result
    def mask_test(self, roc):
        result = [0] * roc.n_pixels
        self.tb.mask_test(5,result)
        return result
    
    @transform_result
    def chip_efficiency(self, roc):
        result = [0] * roc.n_pixels
        trim = roc.trim_bits
        self.tb.init_roc()
        self.tb.chip_efficiency(10,trim,result)
        return result

    def dac_dac(self, roc):
        dac1 = 12
        dac2 = 26  
        dac_range1 = 256 
        dac_range2 = 256
        n_triggers = 5
        n_results = dac_range1*dac_range2
        result = [0] * n_results
        self.tb.arm_pixel(5,5)
        self.tb.dac_dac(dac1, dac_range1, dac2, dac_range2, n_triggers, result)
        self.tb.disarm_pixel(5,5)
        self.tb.init_roc()
        return list_to_grid(dac_range1, dac_range2, result)
