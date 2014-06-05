import PyPxarCore
import logging
import numpy
import sys
import time
from helpers import list_to_matrix

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
        self.load_delays(config)
        self.init_pg(config)
        if not self.initTestboard(pg_setup = self.pg_setup, 
                         power_settings = self.power_settings, 
                         sig_delays = self.sig_delays):
            self.logger.warning("could not init DTB -- possible firmware mismatch.")
            self.logger.warning("Please check if a new FW version is available, exiting...")
            sys.exit(-1)
        self.init_dut(config)
        if eval(config.get('Testboard','hv_on')):
            self.HVon()

    def load_delays(self, config):
        self.sig_delays = {
        "clk":int(config.get('Testboard','clk')),
        "ctr":int(config.get('Testboard','ctr')),
        "sda":int(config.get('Testboard','sda')),
        "tin":int(config.get('Testboard','tin')),
        "deser160phase":int(config.get('Testboard','deser160phase')),
        "triggerdelay":int(config.get('Testboard','triggerdelay'))}
        self.logger.info("Delay settings:\n %s" %self.sig_delays)

    def set_delays(self, config):
        self.load_delays(config)
        self.setTestboardDelays(self.sig_delays)

    def set_delay(self, delay, value):
        self.sig_delays[delay] = value
        self.setTestboardDelays(self.sig_delays)

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
            self.pg_setup = [
                ("resetroc", resr_delay),
                ("calibrate", cal_delay + tct_wbc),
                ("trigger;sync", 0),
                ("calibrate", cal_delay + tct_wbc),
                ("trigger", trg_delay),
                ("calibrate", cal_delay + tct_wbc),
                ("trigger", 0)]
        #Single roc
        else:
            self.pg_setup = [
                ("resetroc",resr_delay),    # PG_RESR
                ("calibrate",cal_delay + tct_wbc), # PG_CAL
                ("trigger",trg_delay),    # PG_TRG
                ("token",0)]
        self.logger.info("Default PG setup:\n %s" %self.pg_setup)
        self.set_pg(self.pg_setup)

    def set_pg(self, pg_setup):
        self.setPatternGenerator(pg_setup)

    def pg_single(self):
        self.daqTrigger(1)
        
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

    def init_roc(self, roc):
        self.logger.info('Initializing ROC: %s' %roc.number)
        pixels = list()
        for pixel in roc.pixels():
            p = PyPxarCore.PixelConfig(pixel.col,pixel.row, max(0,pixel.trim))
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
        self.initDUT(int(config.get('Module','hubid')),config.get('ROC','type'),self.tbm_dacs,config.get('ROC','type'),self.roc_dacs,self.roc_pixels)
        self.mask_dut()
        self.logger.info(self.status())

    def mask_dut(self):
        self.maskAllPixels(False)
        for roc in self.dut.rocs():
            for pixel in roc.pixels():
                if pixel.trim == -1:
                    self.maskPixel(pixel.col, pixel.row, True, roc.number)

    def get_flag(self, xtalk, cals, reverse = False):
        print "xtalk, cals and reverse in get_flag"
        print xtalk
        print cals
        print reverse
        flag = 0x0000
        if cals:
            flag += 0x0002
        if xtalk:
            flag += 0x0004
        if not reverse:
            flag += 0x0008
        print "flag in function get_flag"
        print flag
        return flag
    
    def trim(self, trim_bits):
        self.dut.trim = trim_bits
        for roc in self.dut.rocs():
            trimming = list()
            for pixel in roc.pixels():
                p = [[pixel.col],[pixel.row],[max(0, pixel.trim)]]
                trimming.append(p)
            self.updateTrimBits(trimming, roc.number)

    def get_data(self,Vcal_conversion=False):
        # Initialize variables
        s = self.dut.get_roc_shape()
        hits = []
        phs = []
        # Count decoder errors:
        decoding_errors = 0;
        #a list of ph entries for each of the 16 ROCs
        ph_histo = [[] for x in range(self.dut.n_rocs)]
        ph_cal_histo = [[] for x in range(self.dut.n_rocs)]

        # Blow up the lists to hold the data
        for i in range(self.dut.n_rocs):
            hits.append(numpy.zeros(s))
            phs.append(numpy.zeros(s))

        # Read out the data:
        pixelevents = self.daqGetEventBuffer()
        # Loop over all the PxEvents we got from readout:
        for ievt, evt in enumerate(pixelevents):
            # Count the number of decoding errors:
            decoding_errors += evt.numDecoderErrors
            for ipx, px in enumerate(evt.pixels):
                hits[px.roc_id][px.column][px.row] += 1
                phs[px.roc_id][px.column][px.row] += px.value
                # Appends entry PH > 0 to list of ROC number roc
                if px.value > 0:
                    ph_histo[px.roc_id].append(px.value)
                    if Vcal_conversion:
                        ph_cal = self.dut.roc(px.roc_id).ADC_to_Vcal(px.column, px.row, px.value, self.dut.roc(px.roc_id).ph_slope, self.dut.roc(px.roc_id).ph_offset)
                    else:
                        ph_cal = 0
                    ph_cal_histo[px.roc_id].append(ph_cal)

        self.logger.debug('number of decoding errors %i' %decoding_errors)

        # Clear and return:
        dummy = list() #FIXME: needed? _n_hits _ph _addr
        phs = numpy.nan_to_num(numpy.divide(phs, hits))
        return numpy.array(hits), numpy.array(phs), ph_histo, ph_cal_histo, dummy, dummy, dummy

    def get_calibrate(self, n_triggers, flags = 0):
        self.logger.debug('Calibrate %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        self.testAllPixels(True)
        datas = self.getEfficiencyMap(flags, n_triggers)
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
            dac_range1 = roc.dac(dac1).range
            dac_range2 = roc.dac(dac2).range
            for pixel in roc.active_pixels():
                self.logger.debug('DacDac pix(%s,%s), nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac1, dac_range1, dac2, dac_range2) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                datas = self.getEfficiencyVsDACDAC(roc.dac(dac1).name, 0, dac_range1, roc.dac(dac2).name, 0, dac_range2, flags, n_triggers)
                self.testPixel(pixel.col, pixel.row, False, roc.number)
                pixel.data = numpy.transpose(list_to_matrix(dac_range1+1, dac_range2+1, datas))

    def get_ph_dac(self, n_triggers, dac):
        self.testAllPixels(False)
        for roc in self.dut.rocs():
            dac_range = roc.dac(dac).range
            for pixel in roc.active_pixels():
                self.logger.debug('PHScan pix(%s,%s), nTrig: %s, dac: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac, dac_range) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                datas = self.getPulseheightVsDAC(dac, 0, dac_range, 0x0, n_triggers)
                self.testPixel(pixel.col, pixel.row, False, roc.number)
                pixel.data = numpy.array(datas[roc.number][pixel.col][pixel.row])

    def get_dac_scan(self, n_triggers, dac):
        self.testAllPixels(False)
        for roc in self.dut.rocs():
            dac_range = roc.dac(dac).range
            for pixel in roc.active_pixels():
                self.logger.debug('DacScan pix(%s,%s), nTrig: %s, dac: %s, 0, %s' %(pixel.col,pixel.row, n_triggers, dac, dac_range) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                datas = self.getEfficiencyVsDAC(dac, 0, dac_range, 0x0, n_triggers)
                self.testPixel(pixel.col, pixel.row, False, roc.number)
                pixel.data = numpy.array(datas[roc.number][pixel.col][pixel.row])

    def m_delay(self, value):
        time.sleep(float(value/1000.))

    def u_delay(self, value):
        time.sleep(float(value/1000000.))

    def get_threshold(self, n_triggers, dac, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals, reverse)
        self.testAllPixels(True)
        datas = self.getThresholdMap(dac, flag, n_triggers)
        for roc in self.dut.rocs():
            roc.data = datas[roc.number]
        self.testAllPixels(False)
        return self.dut.data

    def get_pixel_threshold(self, roc, col, row, n_triggers, dac, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals, reverse)
        self.testAllPixels(False)
        self.testPixel(col, row, True, roc)
        datas = self.getThresholdMap(dac, flag, n_triggers)
        self.testPixel(col, row, False, roc)
        return datas[roc][col][row]
       
        #for roc in self.dut.rocs():
        #    for pixel in roc.active_pixels():
        #        self.testPixel(pixel.col, pixel.row, True, roc.number)
        #        datas = self.getThresholdMap(dac, flag, n_triggers)
        #        self.testPixel(pixel.col, pixel.row, False, roc.number)
        #        print datas[roc.number][col][row]
        #        print flag
        #return datas[roc.number][col][row]
        
    def arm_pixel(self, roc, col, row):
        self.testPixel(col, row, True, roc)

    def disarm_pixel(self, roc, col, row):
        self.testPixel(col, row, False, roc)
    
    def ia(self):
        self.logger.info('IA: %.2f mA' %self.get_ia())
    
    def id(self):
        self.logger.info('ID: %.2f mA' %self.get_id())

    def get_ia(self):
        return self.getTBia()*1000.
    
    def get_id(self):
        return self.getTBid()*1000.

    def daq_enable(self):
        self.logger.info('Starting a new DAQ session...')
        return self.daqStart()

    def daq_disable(self):
        self.logger.info('Stopping current DAQ session...')
        return self.daqStop()

    def daq_getbuffer(self):
        return self.daqGetBuffer()

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
            self.m_delay(10)
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


    # Some DAQ functions:
    def pg_stop(self):
        self.daqTriggerLoopHalt()

    def pg_loop(self,period):
        self.daqTriggerLoop(period)

    def pg_setcmd(self,addr,signal,delay=0):
        pg = [(signal,delay)]
        self.set_pg(pg)

    # Some dead functions:
    def select_roc(self,roc):
        pass

    def enable_column(self,col):
        pass

    def init_deser(self):
        pass
