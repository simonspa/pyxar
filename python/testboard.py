import dtb
import logging
import numpy
import sys
from helpers import list_to_matrix

class Testboard(dtb.PyDTB):
    
    def __init__(self, config, dut):
        super(Testboard, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dut = dut
        self.start_dtb(config)
        self._set_max_vals(config)
        self.adjust_sig_level(15)
        self.set_delays(config)
        self.init_pg(config)
        self.init_deser()
        self.pon()
        self.m_delay(400)
        self.reset_off()
        self.m_delay(200)
        if eval(config.get('Testboard','hv_on')):
            self.hv_on()
        self.init_dut(config)

    def start_dtb(self, config):
        request_id = config.get('Testboard','id')
        usb_id = self.find_dtb(request_id)
        if not (usb_id == request_id):
            self.logger.warning('No DTB %s found, using %s instead.' %(request_id, usb_id) )
        if not self.open(usb_id):
            self.logger.error('No DTB %s found, no DTB connected, exiting...' %usb_id)
            sys.exit(-1)
        info_dtb = self.get_info()
        self.logger.info('Using testboard id: %s\n%s' %(usb_id,info_dtb.strip()))

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

    def set_delays(self, config):
        self.sig_delays = {
        "clk":int(config.get('Testboard','clk')),
        "ctr":int(config.get('Testboard','ctr')),
        "sda":int(config.get('Testboard','sda')),
        "tin":int(config.get('Testboard','tin')),
        "deser160phase":int(config.get('Testboard','deser160phase'))}
        self.logger.info("Delay settings:\n %s" %self.sig_delays)
        self.sig_setdelay(self.SIG_CLK, self.sig_delays["clk"])
        self.sig_setdelay(self.SIG_CTR, self.sig_delays["ctr"])
        self.sig_setdelay(self.SIG_SDA, self.sig_delays["sda"])
        self.sig_setdelay(self.SIG_TIN, self.sig_delays["tin"])

    def init_pg(self, config):
        cal_delay = int(config.get('Testboard','pg_cal'))
        tct_wbc = int(config.get('Testboard','tct_wbc'))
        resr_delay = int(config.get('Testboard','pg_resr'))
        trg_delay = int(config.get('Testboard','pg_trg'))
        #Module
        if self.dut.n_tbms > 0:
            self.pg_setcmd(0, self.PG_RESR + resr_delay)
            self.pg_setcmd(1, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(2, self.PG_SYNC + self.PG_TRG)
            self.pg_setcmd(3, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(4, self.PG_TRG  + trg_delay)
            self.pg_setcmd(5, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(6, self.PG_TRG  )
        #Single roc
        else:
            self.pg_setcmd(0, self.PG_RESR + resr_delay);
            self.pg_setcmd(1, self.PG_CAL  + cal_delay + tct_wbc)
            self.pg_setcmd(2, self.PG_TRG  + trg_delay)
            self.pg_setcmd(3, self.PG_TOK);
        self.m_delay(200)

    def init_deser(self):
        deser_phase = self.sig_delays["deser160phase"] 
        if self.dut.n_tbms > 0:
            self.logger.info('Selecting DESER400 for module readout')
            self.daq_select_deser400()
        else:
            self.logger.info('Selecting DESER160 with phase %s for single ROC readout' %deser_phase)
            self.daq_select_deser160(deser_phase)

    def init_tbm(self, tbm, config):
        self.logger.info('Initializing %s' %tbm)
        self.set_tbm_dacs(tbm, config)
    
    def set_tbm_dacs(self, tbm, config):
        #TODO expose to config
        self.tbm_set_DAC(0xE4,0xF0)    #Init TBM, Reset ROC
        self.tbm_set_DAC(0xF4,0xF0)    
        self.tbm_set_DAC(0xE0,0x01)    #Disable PKAM Counter
        self.tbm_set_DAC(0xF0,0x01)    
        self.tbm_set_DAC(0xE2,0xC0)    # Mode = Calibration
        self.tbm_set_DAC(0xF2,0xC0)    
        self.tbm_set_DAC(0xE8,0x10)    # Set PKAM Counter
        self.tbm_set_DAC(0xF8,0x10)    
        self.tbm_set_DAC(0xEA,0x00)    # Delays
        self.tbm_set_DAC(0xFA,0x00)    
        self.tbm_set_DAC(0xEC,0x00)    # Temp measuerement control
        self.tbm_set_DAC(0xFC,0x00)    
        self.m_delay(100)

    # set initial values
    def set_dacs(self, roc):
        self.logger.debug('Setting DACs of %s' %roc)
        for dac in roc.dacs():
            self.logger.debug('Setting dac: %s' %dac)
            self.roc_set_DAC(dac.number, dac.value)
        self.flush()
    
    def set_dac(self, reg, value):
        for roc in self.dut.rocs():
            self.set_dac_roc(roc,reg,value)
        self.flush()

    def set_dac_roc(self,roc,reg,value):
        self.select_roc(roc)
        roc.dac(reg).value = value
        self.logger.debug('Setting %s %s' %(roc, roc.dac(reg)))
        self.roc_set_DAC(roc.dac(reg).number, roc.dac(reg).value)
        self.m_delay(50)

    def select_roc(self, roc):
        #TODO check if roc is already active
        self.i2_c_addr(roc.number)
        self.m_delay(50)

    def init_roc(self, roc):
        self.logger.info('Initializing ROC: %s' %roc.number)
        self.select_roc(roc)
        self.set_dacs(roc)
        self.m_delay(100)
        self.logger.debug('Applying trimming to ROC: %s' %roc)
        #TODO check that the translation to TB is really correct
        self.trim_chip(roc.trim_for_tb)
        self.m_delay(100)
        self.roc_clr_cal()

    def init_dut(self, config):
        if self.dut.n_tbms > 0:
            self.tbm_enable(True)
            self.m_delay(200)
            #TODO expose to config
            self.set_mod_addr(31)
        else:
            self.tbm_enable(False)
            #Just without TBM
            self.set_roc_addr(0)
        self.m_delay(200)
        for tbm in self.dut.tbms():
            self.init_tbm(tbm, config)
        for roc in self.dut.rocs():
            self.init_roc(roc)
    
    def trim(self, trim_bits):
        self.dut.trim = trim_bits
        for roc in self.dut.rocs():
            self.select_roc(roc)
            self.trim_chip(roc.trim_for_tb)
            self.m_delay(100)

    def _mask(self, mask, *args):
        if len(args) == 3:
            roc, col, row = args
            self.dut.pixel(roc,col,row).mask = bool(mask)
        #mask whole chip
        if len(args) == 1:
            roc = args[0]
            self.dut.roc(roc).mask(bool(mask))
        self.trim(self.dut.trim)

    def mask(self, *args):
        self._mask(True, *args)
    
    def unmask(self, *args):
        self._mask(False, *args)

    def get_data(self):
        return self.daq_read_decoded()

    def get_calibrate(self, n_triggers):
        self.logger.debug('Calibrate %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        nhits, average_ph = self.calibrate_parallel(n_triggers, [roc.number for roc in self.dut.rocs()])
        self.dut.data = nhits

    def get_ph(self, n_triggers):
        self.logger.debug('PH %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        nhits, average_ph = self.calibrate_parallel(n_triggers, [roc.number for roc in self.dut.rocs()])
        self.dut.data = average_ph

    def get_ph_roc(self, n_triggers, roc):
        self.select_roc(roc)
        self.logger.debug('PH %s , n_triggers: %s' %(roc, n_triggers) )
        nhits, average_ph = self.calibrate_parallel(n_triggers, [roc.number])
        roc.data = average_ph[roc.number]
        return roc.data

    def get_dac_dac(self, n_triggers, dac1, dac2):
        for roc in self.dut.rocs():
            self.select_roc(roc)
            #TODO TB function has too long vector by one unit
            dac_range1 = roc.dac(dac1).range-1
            dac_range2 = roc.dac(dac2).range-1
            n_results = dac_range1*dac_range2
            self.mask(roc.number)
            for pixel in roc.active_pixels():
                self.unmask(roc.number,pixel.col,pixel.row)
                n_hits = []
                ph_sum = []
                self.logger.debug('DacDac pix(%s,%s), nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac1, dac_range1, dac2, dac_range2) )
                self.dac_dac(n_triggers, pixel.col, pixel.row, roc.dac(dac1).number, dac_range1, roc.dac(dac2).number, dac_range2, n_hits, ph_sum)
                self.set_dac_roc(roc,dac1,roc.dac(dac1).value)
                self.set_dac_roc(roc,dac2,roc.dac(dac2).value)
                pixel.data = numpy.transpose(list_to_matrix(dac_range1, dac_range2, n_hits))
                self.mask(roc.number,pixel.col,pixel.row)
            self.unmask(roc.number)

    def get_ph_dac(self, n_triggers, dac):
        for roc in self.dut.rocs():
            self.select_roc(roc)
            dac_range = roc.dac(dac).range
            for pixel in roc.active_pixels():
                n_hits = []
                ph_sum = []
                self.logger.debug('PHScan pix(%s,%s), nTrig: %s, dac: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac, dac_range) )
                self.dac(n_triggers, pixel.col, pixel.row, roc.dac(dac).number, dac_range,  n_hits, ph_sum)
                self.set_dac_roc(roc,dac,roc.dac(dac).value)
                ph = []
                for p,n in zip(ph_sum,n_hits):
                    if n > 0:
                        ph.append(1.*p/n)
                    else:
                        ph.append(p)
                pixel.data = numpy.array(ph)

    def get_threshold(self, n_triggers, dac, xtalk, cals, reverse):
        #TODO Don't hardcode pars, they will go away with new CTestboard
        start = 0
        step = 1
        if reverse: 
            step = -1
        thr_level = int(n_triggers/2.)
        for roc in self.dut.rocs():
            self.select_roc(roc)
            self.logger.info('Start: %s, step: %s, thr_level: %s, n_triggers: %s, dac: %s, num: %s, xtalk: %s, cals: %s' %(start, step, thr_level, n_triggers, dac, roc.dac(dac).number, xtalk, cals))
            result = [0] * roc.n_pixels
            #TODO remove trimming, they will go away with new CTestboard
            self.chip_threshold(start, step, thr_level, n_triggers, roc.dac(dac).number , xtalk, cals, result)
            self.set_dac_roc(roc,dac,roc.dac(dac).value)
            roc.data = list_to_matrix(roc.n_cols, roc.n_rows, result)
        return self.dut.data

    def get_pixel_threshold(self, roc, col, row, n_triggers, dac, xtalk, cals, reverse):
        #TODO Don't hardcode pars, they will go away with new CTestboard
        start = 0
        step = 1
        if reverse: 
            step = -1
        return self.pixel_threshold(n_triggers, col, row, start, step, n_triggers/2, roc.dac(dac).number, xtalk, cals)

    def arm(self, pixel):
        if not pixel.mask:
            self.arm_pixel(pixel.col, pixel.row)
    
    def disarm(self, pixel):
        self.disarm_pixel(pixel.col, pixel.row)
    
    def ia(self):
        self.logger.info('IA: %.2f mA' %self.get_ia())
    
    def id(self):
        self.logger.info('ID: %.2f mA' %self.get_id())

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
