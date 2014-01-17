import dtb
import logging
import numpy
import sys
from helpers import list_to_matrix
from helpers import decode, decode_full

class Testboard(dtb.PyDTB):
    
    def __init__(self, config, dut):
        super(Testboard, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dut = dut
        self.start_dtb(config)
        self._set_max_vals(config)
        #TODO expose timing to config
        self.adjust_sig_level(10)
        self.set_mhz(4)
        self.init_pg(config)
        self.init_deser()
        #END TODO
        self.pon()
        self.reset_off()
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
        deser_phase = 4
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
        self.m_delay(200)
        self.flush()

    # set initial values
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
            self.set_dac_roc(roc,reg,value)

    def set_dac_roc(self,roc,reg,value):
        self.select_roc(roc)
        roc.dac(reg).value = value
        self.logger.debug('Setting %s %s' %(roc, roc.dac(reg)))
        self.roc_set_DAC(roc.dac(reg).number, roc.dac(reg).value)
        self.m_delay(50)

    def select_roc(self, roc):
        #TODO check if roc is already active
        self.i2_c_addr(roc.number)
        #self.m_delay(20)
        #if self.dut.n_tbms == 0:
        #    self.set_roc_addr(0)

    def init_roc(self, roc):
        self.logger.info('Initializing ROC: %s' %roc.number)
        self.select_roc(roc)
        self.set_dacs(roc)
        self.flush()
        self.m_delay(100)
        self.logger.debug('Applying trimming to ROC: %s' %roc)
        #TODO check that the translation to TB is really correct
        self.trim_chip(roc.trim_for_tb)
        self.m_delay(200)
        self.flush()
        self.roc_clr_cal()
        self.flush()

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
        self.flush()
        for tbm in self.dut.tbms():
            self.init_tbm(tbm, config)
        for roc in self.dut.rocs():
            self.init_roc(roc)
    
    def trim(self, trim_bits):
        self.dut.trim = trim_bits
        for roc in self.dut.rocs():
            #TODO check that the translation to TB is really correct
            self.trim_chip(roc.trim_for_tb)

    #def get_calibrate(self, n_triggers):
    #    self.daq_enable() 
    #    n_hits = []
    #    ph = []
    #    address = []
    #    for col in range(self.dut.roc(0).n_cols):
    #        for row in range(self.dut.roc(0).n_rows):
    #            for roc in self.dut.rocs():
    #                self.select_roc(roc)
    #                if row > 0:
    #                    self.roc_clr_cal();
    #                    self.disarm_pixel(col,row-1)
    #                self.arm_pixel(col,row)
    #            self.calibrate(n_triggers, n_hits, ph, address)

    #        for roc in self.dut.rocs():
    #            self.select_roc(roc)
    #            self.roc_clr_cal();
    #            self.disarm_pixel(col,self.dut.roc(0).n_rows)

    #    self.daq_disable()

    #    #for roc in self.dut.rocs():
    #    self.logger.debug('decoding')
    #    #todo: 16
    #    datas = decode_full(16,roc.n_cols, roc.n_rows, address, n_hits)
    #    for roc in self.dut.rocs():
    #        roc.data = datas[roc.number]

    def get_calibrate(self, n_triggers):
        for roc in self.dut.rocs():
            self.select_roc(roc)
            n_hits = []
            ph = []
            address = []
            self.logger.debug('Calibrate %s'%roc)
            self.calibrate(n_triggers, n_hits, ph, address)
            roc.data = decode(roc.n_cols, roc.n_rows, address, n_hits)

    def get_ph(self, n_triggers):
        for roc in self.dut.rocs():
            self.select_roc(roc)
            n_hits = []
            ph_sum = []
            address = []
            self.calibrate(n_triggers, n_hits, ph_sum, address)
            ph = []
            for p,n in zip(ph_sum,n_hits):
                if n > 0:
                    ph.append(p/n)
                else:
                    ph.append(p)
            roc.data = decode(roc.n_cols, roc.n_rows, address, ph)

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
                self.set_dac_roc(roc,dac1,roc.dac(dac1).value)
                self.set_dac_roc(roc,dac2,roc.dac(dac2).value)
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
            self.logger.info('Start: %s, step: %s, thr_level: %s, n_triggers: %s, dac: %s, num: %s, xtalk: %s, cals: %s' %(start, step, thr_level, n_triggers, dac, roc.dac(dac).number, xtalk, cals))
            result = [0] * roc.n_pixels
            #TODO remove trimming, they will go away with new CTestboard
            trim = roc.trim_for_tb 
            self.chip_threshold(start, step, thr_level, n_triggers, roc.dac(dac).number , xtalk, cals, trim, result)
            self.set_dac_roc(roc,dac,roc.dac(dac).value)
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
