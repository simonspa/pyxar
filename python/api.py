import PyPxarCore
from PyPxarCore import *
import logging
import numpy
import sys
import time
from helpers import list_to_matrix

class api(PyPxarCore):
    
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
                ("trigger;sync", 0)]
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

    def pg_single(self, nTrig, period):
        self.daqTrigger(nTrig, period)
        
    def init_tbm(self, config):
        #TODO move to config
        self.tbm_dacs = [{

        #settings for tbm 08
        #"clear":0xF0,       # Init TBM, Reset ROC
        #"counters":0x01,    # Disable PKAM Counter
        #"mode":0xC0,        # Set Mode = Calibration
        #"pkam_set":0x10,    # Set PKAM Counter
        #"delays":0x00,      # Set Delays
        #"temperature": 0x00 # Turn off Temperature Measurement

        #settings for tbm 08b (suggestion by Martino Dell Osso)
        "clear": 0xF0,       # Init TBM, Reset ROC
        "counters": 0x81,    # Disable PKAM Counter
        "mode": 0xC0,        # Set Mode = Calibration
        "pkam_set": 0x10,    # Set PKAM Counter
        "delays": 0xE4,      # Set Delays
        "basee": 0x20,       # adjust phase of internal 160MHz clock. Beat:0x24 
        "temperature": 0x00  # Turn off Temperature Measurement
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
            p = PixelConfig(pixel.col,pixel.row, max(0,pixel.trim))
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
        self.initDUT(int(config.get('Module','hubid')),config.get('TBM','type'),self.tbm_dacs,config.get('ROC','type'),self.roc_dacs,self.roc_pixels)
        self.mask_dut()
        self.logger.info(self.status())

    def mask_dut(self):
        self.maskAllPixels(False)
        for roc in self.dut.rocs():
            for pixel in roc.pixels():
                if pixel.trim == -1:
                    self.maskPixel(pixel.col, pixel.row, True, roc.number)

    def get_flag(self, xtalk, cals, reverse = False):
        flag = 0x0000
        if cals:
            flag += FLAG_CALS
        if xtalk:
            flag += FLAG_XTALK
        if not reverse:
            flag += FLAG_RISING_EDGE
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
            #decoding_errors += evt.numDecoderErrors
            for ipx, px in enumerate(evt.pixels):
                hits[px.roc][px.column][px.row] += 1
                phs[px.roc][px.column][px.row] += px.value
                # Appends entry PH > 0 to list of ROC number roc
                if px.value > 0:
                    ph_histo[px.roc].append(px.value)
                    if Vcal_conversion:
                        ph_cal = self.dut.roc(px.roc).ADC_to_Vcal(px.column, px.row, px.value, self.dut.roc(px.roc).ph_slope, self.dut.roc(px.roc).ph_offset, self.dut.roc(px.roc).ph_par2)
                    else:
                        ph_cal = 0
                    ph_cal_histo[px.roc].append(ph_cal)

        #self.logger.debug('number of decoding errors %i' %decoding_errors)

        # Clear and return:
        dummy = list() #FIXME: needed? _n_hits _ph _addr
        phs = numpy.nan_to_num(numpy.divide(phs, hits))
        return numpy.array(hits), numpy.array(phs), ph_histo, ph_cal_histo, dummy, dummy, dummy


    def get_calibrate(self, n_triggers, flags = 0):
        self.logger.debug('Calibrate %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        self.testAllPixels(True)
        datas = self.getEfficiencyMap(flags, n_triggers)
        for roc in self.dut.rocs():
            roc.data = numpy.zeros((52,80))
        for px in datas:
            self.dut.roc(px.roc).data[px.column][px.row] = px.value
        self.testAllPixels(False)

    def get_ph(self, n_triggers):
        self.logger.debug('PH %s , n_triggers: %s' %(self.dut.n_rocs, n_triggers) )
        self.testAllPixels(True)
        datas = self.getPulseheightMap(0x0, n_triggers)
        for roc in self.dut.rocs():
            roc.data = numpy.zeros((52,80))
        for px in datas:
            self.dut.roc(px.roc).data[px.column][px.row] = px.value
        self.testAllPixels(False)

    def get_ph_roc(self, n_triggers, roc):
        self.testAllPixels(True, roc.number)
        datas = self.getPulseheightMap(0x0, n_triggers)
        self.testAllPixels(False)
        self.dut.roc(roc.number).data = numpy.zeros((52,80))
        for px in datas:
            self.dut.roc(roc.number).data[px.column][px.row] = px.value
        #roc.data = datas[roc.number]
        roc.data = self.dut.roc(roc.number).data
        return roc.data

    def get_dac_dac(self, n_triggers, dac1, dac2):
        self.testAllPixels(False)
        flags = 0x0
        for roc in self.dut.rocs():
            dac_range1 = roc.dac(dac1).range
            dac_range2 = roc.dac(dac2).range
            for pixel in roc.active_pixels():
                self.logger.debug('DacDac pix(%s,%s) of %s, nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, roc, n_triggers, dac1, dac_range1, dac2, dac_range2) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)

        datas = self.getEfficiencyVsDACDAC(roc.dac(dac1).name, 1, 0, dac_range1, roc.dac(dac2).name, 1, 0, dac_range2, flags, n_triggers)
        for pixel in roc.active_pixels():
            self.testPixel(pixel.col, pixel.row, False, roc.number)

        efficiency = []
        datas = datas.tolist()
        for idac, dac in enumerate(datas):
            found = False
            for px in dac:
                if px.column == pixel.col and px.row == pixel.row and px.roc == roc.number:
                    efficiency.append(px.value)
                    found = True
            if found == False:
                efficiency.append(0)
        pixel.data = numpy.transpose(list_to_matrix(dac_range1+1, dac_range2+1, efficiency))

    def get_ph_dac(self, n_triggers, dac):
        self.testAllPixels(False)
        #activate pixels to be tested
        for roc in self.dut.rocs():
            dac_range = roc.dac(dac).range
            for pixel in roc.active_pixels():
                self.logger.debug('PHScan pix(%s,%s) of %s, nTrig: %s, dac: %s, 0, %s' %(pixel.col,pixel.row, roc, n_triggers, dac, dac_range) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
        #do test for all activated pixels 
        datas = self.getPulseheightVsDAC(dac, 1, 0, dac_range, 0x0, n_triggers)
        #deactivate all pixels
        self.testAllPixels(False)
        #extract pulse height from returned data 
        for roc in self.dut.rocs():
            for pixel in roc.active_pixels():  
                pulseheight = []
                if type(datas) == numpy.ndarray:
                    datas = datas.tolist()
                for idac, dac in enumerate(datas):
                    found = False
                    for px in dac:
                        if px.column == pixel.col and px.row == pixel.row and px.roc == roc.number:
                            pulseheight.append(px.value)
                            found = True
                    if found == False:
                        pulseheight.append(0)
                pixel.data = numpy.array(pulseheight)

    def get_ph_dacdac(self, n_triggers, dac1, dac2):
        self.testAllPixels(False)
        #activate pixels to be tested
        for roc in self.dut.rocs():
            dac1_range = roc.dac(dac1).range
            dac2_range = roc.dac(dac2).range
            for pixel in roc.active_pixels():
                self.logger.debug('PHDacDac pix(%s,%s) of %s, nTrig: %s, dac1: %s, 0, %s, dac2: %s, 0, %s' %(pixel.col,pixel.row, roc, n_triggers, dac1, dac1_range, dac2, dac2_range) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
                self.maskPixel(pixel.col, pixel.row, False, roc.number)
                #do test for all activated pixels 
                datas = self.getPulseheightVsDACDAC(dac1, 1, 0, dac1_range, dac2, 1, 0, dac2_range, 0x0, n_triggers)
                #deactivate all pixels
                for pixel in roc.active_pixels():
                    self.testPixel(pixel.col, pixel.row, False, roc.number)
                #extract pulse height from returned data 
                pulseheight = []
                if type(datas) == numpy.ndarray:
                    datas = datas.tolist()
                for idac, dac in enumerate(datas):
                    found = False
                    for px in dac:
                        pulseheight.append(px.value)
                pixel.data = numpy.transpose(list_to_matrix(dac1_range+1, dac2_range+1, pulseheight))

       

    def get_dac_scan(self, n_triggers, dac):
        self.testAllPixels(False)
        #activate pixels to be tested
        for roc in self.dut.rocs():
            dac_range = roc.dac(dac).range
            for ipx, pixel in enumerate(roc.active_pixels()):
                self.logger.debug('DacScan pix(%s,%s) of %s, nTrig: %s, dac: %s, 0, %s' %(pixel.col,pixel.row, roc, n_triggers, dac, dac_range) )
                self.testPixel(pixel.col, pixel.row, True, roc.number)
        #do test for all activated pixels
        datas = self.getEfficiencyVsDAC(dac, 1, 0, dac_range, 0x0, n_triggers)
        #deactivate all pixels
        self.testAllPixels(False)
        #extract efficiencies from returned data
        for roc in self.dut.rocs():
            for ipx, pixel in enumerate(roc.active_pixels()):
                efficiency = []
                datas = datas.tolist()
                for idac, dac in enumerate(datas):
                    found = False
                    for px in dac:
                        if px.column == pixel.col and px.row == pixel.row and px.roc == roc.number:
                            efficiency.append(px.value)
                            found = True
                    if found == False:
                        efficiency.append(0)
                pixel.data = numpy.array(efficiency)

    def m_delay(self, value):
        time.sleep(float(value/1000.))

    def u_delay(self, value):
        time.sleep(float(value/1000000.))

    def get_threshold(self, n_triggers, dac, threshold, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals, reverse)
        self.testAllPixels(True)
        # FIXME "roc" is not known here
        #dac_range = roc.dac(dac).range
        dac_range = 255
        datas = self.getThresholdMap(dac, 1, 0, dac_range, threshold, flag, n_triggers)
        self.testAllPixels(False)
        for roc in self.dut.rocs():
            roc.data = numpy.zeros((52,80))
        for px in datas:
            self.dut.roc(px.roc).data[px.column][px.row] = px.value
        return self.dut.data

    def get_pixel_threshold(self, roc, col, row, n_triggers, dac, threshold, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals, reverse)
        self.testAllPixels(False)
        self.testPixel(col, row, True, roc.number)
        dac_range = roc.dac(dac).range
        datas = self.getThresholdMap(dac, 1, 0, dac_range, threshold, flag, n_triggers)
        self.testPixel(col, row, False, roc.number)
        for px in datas:
            if (px.roc == roc.number and px.column == col and px.row == row):
                return px.value
     
    def get_single_pixel_threshold(self, roc, col, row, n_triggers, dac, threshold, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals, reverse)
        self.testAllPixels(False)
        self.testPixel(col, row, True, roc)
        dac_range = 255
        datas = self.getThresholdMap(dac, 1, 0, dac_range, threshold, flag, n_triggers)
        self.testPixel(col, row, False, roc)
        for px in datas:
            if (px.roc == roc and px.column == col and px.row == row):
                self.logger.info('threshold: %i' % px.value)

    def get_single_pixel_threshold_vs_dac(self, roc, col, row, n_triggers, dac, dac2, dac2min, dac2max, threshold, xtalk, cals, reverse):
        flag = self.get_flag(xtalk, cals, reverse)
        self.testAllPixels(False)
        self.testPixel(col, row, True, roc)
        dac_range = 255
        datas = self.getThresholdVsDAC(dac, 1, 0, dac_range, dac2, 1, dac2min, dac2max, threshold, flag, n_triggers)
        self.testPixel(col, row, False, roc)
        #extract thresholds from returned data
        for roc in self.dut.rocs():
            for ipx, pixel in enumerate(roc.active_pixels()):
                threshold = []
                for idac, dac in enumerate(datas):
                    found = False
                    for px in dac:
                        if px.column == pixel.col and px.row == pixel.row and px.roc == roc.number:
                            threshold.append(px.value)
                            found = True
                    if found == False:
                        threshold.append(0)
                pixel.data = numpy.array(threshold)
       
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

    def set_external_clk(self, enable):
        self.setExternalClock(enable)

    def set_signal_mode(self, signal, mode):
        self.setSignalMode(signal, mode)

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
        self.logger.debug('This function is not needed when using pxarCore. Remove if you want.')
        pass

    def enable_column(self,col):
        self.logger.debug('This function is not needed when using pxarCore. Remove if you want.')
        pass

    def init_deser(self):
        self.logger.debug('This function is not needed when using pxarCore. Remove if you want.')
        pass
