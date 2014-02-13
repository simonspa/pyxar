import PyPxarCore
import logging
import numpy
import sys
import time

class api(PyPxarCore.PyPxarCore):
    
    def __init__(self, config, dut):
        super(api, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(self.getVersion())
        self.config = None
        self.tbm_dacs = []
        self.roc_pixels = list()
        self.roc_dacs = list()

    def startup(self, config, dut):
        self.config = config
        self.dut = dut
        self._set_max_vals(config)
        #TODO
        #self.adjust_sig_level(15)
        self.set_mhz(4)
        self.init_pg(config)
        self.Pon()
        if eval(config.get('Testboard','hv_on')):
            self.HVon()
        if not self.initTestboard(pg_setup = self.pg_setup, 
                         power_settings = self.power_settings, 
                         sig_delays = self.sig_delays):
            self.logger.warning("could not init DTB -- possible firmware mismatch.")
            self.logger.warning("Please check if a new FW version is available, exiting...")
            sys.exit(-1)
        self.init_dut(config)

    def set_mhz(self, value):
        #TODO move to config
        self.sig_delays = {
        "clk":value,
        "ctr":value,
        "sda":value+15,
        "tin":value+5,
        "deser160phase":4}

    def _set_max_vals(self, config):
        max_ia = int(config.get('Testboard','max_ia'))
        max_id = int(config.get('Testboard','max_id'))
        max_va = int(config.get('Testboard','max_va'))
        max_vd = int(config.get('Testboard','max_vd'))
        self.logger.info('Max IA: %s' %max_ia)
        self.logger.info('Max ID: %s' %max_id)
        self.logger.info('Max VA: %s' %max_va)
        self.logger.info('Max VD: %s' %max_vd)
        self.power_settings = {
        "va":max_va/1000.,
        "vd":max_vd/1000.,
        "ia":max_ia/1000.,
        "id":max_id/1000.}

    def __del__(self):
        self.logger.info("Deleting testboard")
        self.HVoff()
        self.Poff()

    def init_pg(self, config):
        cal_delay = int(config.get('Testboard','pg_cal'))
        tct_wbc = int(config.get('Testboard','tct_wbc'))
        resr_delay = int(config.get('Testboard','pg_resr'))
        trg_delay = int(config.get('Testboard','pg_trg'))
        #Module
        if self.dut.n_tbms > 0:
            #TODO adapt as below
            self.pg_setcmd(0, self.PG_RESR + resr_delay)
            self.pg_setcmd(1, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(2, self.PG_SYNC + self.PG_TRG)
            self.pg_setcmd(3, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(4, self.PG_TRG  + trg_delay)
            self.pg_setcmd(5, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(6, self.PG_TRG  )
        #Single roc
        else:
            self.pg_setup = {
            0x0800:resr_delay,    # PG_RESR
            0x0400:cal_delay + tct_wbc, # PG_CAL
            0x0200:trg_delay,    # PG_TRG
            0x0100:0}

    def init_tbm(self, config):
        #TODO move to config
        self.tbm_dacs = [{
        "clear":0xF0,       # Init TBM, Reset ROC
        "counters":0x01,    # Disable PKAM Counter
        "mode":0xC0,        # Set Mode = Calibration
        "pkam_set":0x10,    # Set PKAM Counter
        "delays":0x00,      # Set Delays
        "temperature": 0x00 # Turn off Temperature Measurement
        }]
    
    def set_dacs(self, roc):
        self.logger.debug('Setting DACs of %s' %roc)
        for dac in roc.dacs():
            self.logger.debug('Setting dac: %s' %dac)
            self.roc_set_DAC(dac.number, dac.value)
    
    def set_dac(self, reg, value):
        for roc in self.dut.rocs():
            self.set_dac_roc(roc,reg,value)

    def set_dac_roc(self,roc,reg,value):
        roc.dac(reg).value = value
        self.logger.debug('Setting %s %s' %(roc, roc.dac(reg)))
        self.setDAC(roc.dac(reg).name, roc.dac(reg).value, roc.number)
        self.m_delay(50)

    def init_roc(self, roc):
        self.logger.info('Initializing ROC: %s' %roc.number)
        pixels = list()
        for pixel in roc.pixels():
            p = PyPxarCore.PixelConfig(pixel.col,pixel.row, pixel.trim)
            pixels.append(p)
        self.roc_pixels.append(pixels)
        dacs = {}
        for dac in roc.dacs():
            dacs[dac.name] = dac.value
        self.roc_dacs.append(dacs)

    def init_dut(self, config):
        for tbm in self.dut.tbms():
            self.init_tbm(config)
        for roc in self.dut.rocs():
            self.init_roc(roc)
        #TODO add ROC type to config
        self.initDUT("tbm08",self.tbm_dacs,"psi46digv2",self.roc_dacs,self.roc_pixels)
        self.programDUT()
        self.logger.info(self.status())

    def get_flag(self, xtalk, cals):
        flag = 0x0000
        if cals:
            flag += 0x0002
        if xtalk:
            flag += 0x0004
    
    def trim(self, trim_bits):
        self.dut.trim = trim_bits
        for roc in self.dut.rocs():
            trimming = list()
            for pixel in roc.pixels():
                p = PyPxarCore.PixelConfig(pixel.col,pixel.row, pixel.trim)
                trimming.append(p)
            self.updateTrimBits(trimming, roc.number);

    def get_data(self):
        self.logger.warning("HR functionality not yet implemented in api version, exiting...")
        sys.exit(-1)

    def get_calibrate(self, n_triggers):
        self.logger.debug('Calibrate %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        self.testAllPixels(True)
        datas = self.getEfficiencyMap(0, n_triggers)
        for roc in self.dut.rocs():
            roc.data = datas[roc.number]
        self.testAllPixels(False)

    def get_ph(self, n_triggers):
        self.logger.debug('PH %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        self.testAllPixels(True)
        datas = self.getPulseheightMap(0x0, n_triggers)
        for roc in self.dut.rocs():
            roc.data = datas[roc.number]
        self.testAllPixels(False)

    def get_ph_roc(self, n_triggers, roc):
        self.testAllPixels(True, roc.number)
        datas = self.getPulseheightMap(0x0, n_triggers)
        self.testAllPixels(False)
        roc.data = datas[roc.number]

    def get_dac_dac(self, n_triggers, dac1, dac2):
        self.testAllPixels(False)
        flags = 0x0
        for roc in self.dut.rocs():
            #TODO TB function has too long vector by one unit
            dac_range1 = roc.dac(dac1).range-1
            dac_range2 = roc.dac(dac2).range-1
            for pixel in roc.active_pixels():
                self.logger.debug('DacDac pix(%s,%s), nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac1, dac_range1, dac2, dac_range2) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                datas = self.getEfficiencyVsDACDAC(roc.dac(dac1).name, 0, dac_range1, roc.dac(dac2).name, 0, dac_range2, flags, n_triggers)
                self.testPixel(pixel.col, pixel.row, False, roc.number)
                self.set_dac_roc(roc,dac1,roc.dac(dac1).value)
                self.set_dac_roc(roc,dac2,roc.dac(dac2).value)
                pixel.data = datas[roc.number][pixel.col][pixel.row]

    def get_ph_dac(self, n_triggers, dac):
        self.testAllPixels(False)
        for roc in self.dut.rocs():
            dac_range = roc.dac(dac).range
            for pixel in roc.active_pixels():
                self.logger.debug('PHScan pix(%s,%s), nTrig: %s, dac: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac, dac_range) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                datas = self.getPulseheightVsDAC(dac, 0, roc.dac(dac).range, 0x0, n_triggers)
                self.testPixel(pixel.col, pixel.row, False, roc.number)
                self.set_dac_roc(roc,dac,roc.dac(dac).value)
                pixel.data = numpy.array(datas[roc.number][pixel.col][pixel.row])

    def m_delay(self, value):
        time.sleep(float(value/1000.))

    def get_threshold(self, n_triggers, dac, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals)
        self.testAllPixels(True)
        datas = self.getThresholdMap(dac, flag, n_triggers)
        for roc in self.dut.rocs():
            roc.data = datas[roc.number]
        self.testAllPixels(False)
        return self.dut.data

    def get_pixel_threshold(self, roc, col, row, n_triggers, dac, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals)
        self.testAllPixels(False)
        for roc in self.dut.rocs():
            for pixel in roc.active_pixels():
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                datas = self.getThresholdMap(dac, flag, n_triggers)
                self.testPixel(pixel.col, pixel.row, False, roc.number)
        return datas[roc.number][col][row]
        
    def arm(self, pixel):
        pass
    
    def disarm(self, pixel):
        pass
    
    def ia(self):
        self.logger.info('IA: %.2f mA' %self.get_ia())
    
    def id(self):
        self.logger.info('ID: %.2f mA' %self.get_id())

    def get_ia(self):
        self.m_delay(100)
        return self.getTBia()*1000.
    
    def get_id(self):
        self.m_delay(100)
        return self.getTBid()*1000.

    def binary_search(self, roc, dac, set_value, function, inverted = False):
        '''Runs a binary search on roc changing a dac until function = set_value. 
        Inverted controls if function rises with increasing dac.'''
        self.logger.info('%s Running binary search in dac %s until %s = %s, reverted = %s' %(roc, dac, set_value, function.__name__, inverted))
        low = 1
        high = roc.dac(dac).range -1
        #Binary search to find value
        while low<high:
            average_dac = (high+low)//2
            self.set_dac_roc(roc, dac, average_dac)
            value = function()
            self.logger.debug('%s = %s, value = %s'%(dac, average_dac, value))
            if value > set_value:
                if inverted:
                    low = average_dac+1
                else:
                    high = average_dac-1
            elif value < set_value:
                if inverted:
                    high = average_dac-1
                else:
                    low = average_dac+1
            else:
                break
        return average_dac
