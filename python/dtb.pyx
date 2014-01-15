from libcpp cimport bool
from libcpp.vector cimport vector
from libc.stdint cimport uint8_t, int8_t, uint16_t, int16_t, int32_t, uint32_t
from libc.stdlib cimport malloc, free
from libcpp.string cimport string


cdef extern from "pixel_dtb.h":
    cdef cppclass CTestboard:
        CTestboard()
        bool FindDTB(string &usbId) except +
        bool Open(string &usbId) except +
        void Close() except +
        void Welcome() except +
        void Flush() except +
        void Init() except +
        void Pon() except +
        void Poff() except +
        void HVon() except +
        void HVoff() except +
        void ResetOn() except +
        void ResetOff() except +
        void mDelay(uint16_t) except +
        void SetVA(double) except +
        void SetVD(double) except +
        void SetIA(double) except +
        void SetID(double) except +
        double GetVA() except +
        double GetVD() except +
        double GetIA() except +
        double GetID() except +
        void SetMHz(int) except +
        void Pg_SetCmd(uint16_t addr, uint16_t cmd) except +
        void roc_I2cAddr(uint8_t) except +
        void SetRocAddress(uint8_t) except +
        void roc_SetDAC(uint8_t, uint8_t) except +
        void roc_ClrCal() except +
        void roc_Chip_Mask() except +
        void Daq_Select_Deser160(uint8_t shift) except +
        void Daq_Select_Deser400() except +
        uint32_t Daq_Open(uint32_t buffersize, uint8_t channel) except +
        void Daq_Close(uint8_t channel) except +
        void Daq_Start(uint8_t channel) except +
        void Daq_Stop(uint8_t channel) except +
        void Sig_SetLevel(uint8_t signal, uint8_t level) except +
        void tbm_Enable(bool on) except +
        void mod_Addr(uint8_t hub) except +
        void tbm_Set(uint8_t reg, uint8_t value) except +
        void EnableColumn(int) except +
        void ArmPixel(int, int) except +
        void DisarmPixel(int, int) except +
        int8_t CalibrateDacDacScan(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, vector[int16_t] &, vector[int32_t] &) 
        int16_t CalibrateMap(int16_t, vector[int16_t] &, vector[int32_t] &, vector[uint32_t] &) 
        int16_t TrimChip(vector[int16_t] &) except + 
        int8_t TrimChip_Sof(vector[int16_t] &)
        int32_t MaskTest(int16_t, int16_t*) 
        int32_t ChipThreshold(int32_t, int32_t, int32_t, int32_t, int32_t, int32_t, int32_t, int32_t *, int32_t *)
        int32_t PixelThreshold(int32_t col, int32_t row, int32_t start, int32_t step, int32_t thrLevel, int32_t nTrig, int32_t dacReg, int32_t xtalk, int32_t cals, int32_t trim)
        int8_t CalibrateMap_Sof(int16_t, vector[int16_t] &, vector[int32_t] &, vector[uint32_t] &) 
        int8_t CalibrateDacDacScan_Sof(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, vector[int16_t] &, vector[int32_t] &) 
    cdef int PG_TOK 
    cdef int PG_TRG 
    cdef int PG_RESR 
    cdef int PG_CAL 
    cdef int PG_SYNC 
    cdef int SIG_SDA
    cdef int SIG_CTR
    cdef int SIG_CLK
    cdef int SIG_TIN


cdef class PyDTB: 
    cdef CTestboard *thisptr
    def __cinit__(self): 
        self.thisptr = new CTestboard()
        self.PG_TOK = PG_TOK
        self.PG_TRG = PG_TRG
        self.PG_RESR = PG_RESR
        self.PG_CAL = PG_CAL
        self.PG_SYNC = PG_SYNC

    def __dealloc__(self): 
        del self.thisptr
    
    def find_dtb(self,usbId):
        return  self.thisptr.FindDTB(usbId)
        
    def open(self,usbId):
        self.thisptr.Open(usbId)
        self.thisptr.Init()
        self.thisptr.Flush()
        self.thisptr.Welcome()
        self.thisptr.Flush()
        return True
    
    def cleanup(self):
        self.thisptr.Close()
    
    def flush(self):
        self.thisptr.Flush()
    
    def m_delay(self, value):
        self.thisptr.mDelay(value)
        self.thisptr.Flush()
    
    def i2_c_addr(self,identity):
        self.thisptr.roc_I2cAddr(identity)
        self.thisptr.Flush()
    
    def set_roc_addr(self, identity):
        self.thisptr.SetRocAddress(identity)
        self.thisptr.Flush()
    
    def roc_set_DAC(self, reg, value):
        self.thisptr.roc_SetDAC(reg, value)
        self.thisptr.Flush()

    def roc_clr_cal(self):
        self.thisptr.roc_ClrCal()
        self.thisptr.Flush()
    
    def roc_chip_mask(self):
        self.thisptr.roc_Chip_Mask()
        self.thisptr.Flush()
    
    def set_mod_addr(self, identity):
        self.thisptr.mod_Addr(identity)
        self.thisptr.Flush()

    def adjust_sig_level(self, level):
        self.thisptr.Sig_SetLevel(SIG_SDA, level)
        self.thisptr.Sig_SetLevel(SIG_CTR, level)
        self.thisptr.Sig_SetLevel(SIG_CLK, level)
        self.thisptr.Sig_SetLevel(SIG_TIN, level)
        self.thisptr.Flush()
    
    def tbm_set_DAC(self, reg, value):
        self.thisptr.tbm_Set(reg, value)
        self.thisptr.Flush()

    def tbm_enable(self, on):
        self.thisptr.tbm_Enable(on)
        self.thisptr.Flush()

    def daq_select_deser160(self, shift):
        self.thisptr.Daq_Select_Deser160(shift)
        self.thisptr.Flush()
    
    def daq_select_deser400(self):
        self.thisptr.Daq_Select_Deser400()
        self.thisptr.Flush()
    
    def daq_enable(self):
        self.thisptr.Daq_Open(32470, 0)
        self.thisptr.Daq_Open(32470, 1)
        self.thisptr.Daq_Start(0)
        self.thisptr.Daq_Start(1)
        self.thisptr.Flush()
    
    def daq_disable(self):
        self.thisptr.Daq_Stop(0)
        self.thisptr.Daq_Stop(1)
        self.thisptr.Daq_Close(0)
        self.thisptr.Daq_Close(1)
        self.thisptr.Flush()
    
    def set_mhz(self, value):
        self.thisptr.SetMHz(value)
        self.thisptr.Flush()
    
    def pg_setcmd(self, addr, cmd):
        self.thisptr.Pg_SetCmd(addr, cmd)
        self.thisptr.Flush()
    
    def pon(self):
        self.thisptr.Pon()
        self.thisptr.Flush()

    def poff(self):
        self.thisptr.Poff()
        self.thisptr.Flush()
    
    def hv_on(self):
        self.thisptr.HVon()
        self.thisptr.Flush()

    def hv_off(self):
        self.thisptr.HVoff()
        self.thisptr.Flush()
    
    def set_id(self, value):
        self.thisptr.SetID(value)
        self.thisptr.Flush()

    def set_vd(self, value):
        self.thisptr.SetVD(value)
        self.thisptr.Flush()
    
    def set_ia(self, value):
        self.thisptr.SetIA(value)
        self.thisptr.Flush()

    def set_va(self, value):
        self.thisptr.SetVA(value)
        self.thisptr.Flush()

    def get_ia(self):
        return_value = self.thisptr.GetIA()*1000.
        self.thisptr.Flush()
        return return_value
    
    def get_id(self):
        return_value =  self.thisptr.GetID()*1000.
        self.thisptr.Flush()
        return return_value
    
    def get_va(self):
        return_value = self.thisptr.GetVA()
        self.thisptr.Flush()
        return return_value
    
    def get_vd(self):
        return_value = self.thisptr.GetVD()
        self.thisptr.Flush()
        return return_value
    
    def reset_on(self):
        self.thisptr.ResetOn()
        self.thisptr.Flush()

    def reset_off(self):
        self.thisptr.ResetOff()
        self.thisptr.Flush()
    
    def arm_pixel(self, col, row):
        self.thisptr.EnableColumn(col)
        self.thisptr.ArmPixel(col, row)
        self.thisptr.Flush()
    
    def disarm_pixel(self, col, row):
        self.thisptr.DisarmPixel(col, row)
        self.thisptr.Flush()
        
    def chip_threshold(self, start, step, thr_level, n_triggers, dac_reg, xtalk, cals, trim, result):
        cdef int32_t *data
        cdef int32_t *trim_bits
        n = len(result) 
        n_trim = len(trim) 
        data = <int32_t *>malloc(n*sizeof(int))
        trim_bits = <int32_t *>malloc(n_trim*sizeof(int))
        for i in xrange(n_trim):
            trim_bits[i] = trim[i]
        return_value = self.thisptr.ChipThreshold(start, step, thr_level, n_triggers, dac_reg, xtalk, cals, trim_bits, data)
        self.thisptr.Flush()
        for i in xrange(n):
            result[i] = data[i] 
        free(data)
        free(trim_bits)
        return return_value
    
    def trim_chip(self, trim):
        cdef vector[int16_t] trim_bits
        cdef int16_t bit
        for bit in trim:
            trim_bits.push_back(bit)
        return_value = self.thisptr.TrimChip(trim_bits)
        self.thisptr.Flush()
        return return_value

    def calibrate(self,n_triggers, num_hits, ph, addr):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        cdef vector[uint32_t] adr
        return_value = self.thisptr.CalibrateMap_Sof(n_triggers, n_hits, ph_sum, adr)
        self.thisptr.Flush()
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
            addr.append(adr[i]) 
        return return_value

    def dac_dac(self, n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, num_hits, ph):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        return_value = self.thisptr.CalibrateDacDacScan_Sof(n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, n_hits, ph_sum)
        #return_value = self.thisptr.CalibrateDacDacScan(n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, n_hits, ph_sum)
        self.thisptr.Flush()
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
        return return_value

    def pixel_threshold(self, n_triggers, col, row, start, step, thrLevel, dacReg, xtalk, cals, trim):
        return_value = self.thisptr.PixelThreshold(col ,row, start, step, thrLevel, n_triggers, dacReg, xtalk, cals, trim)
        self.thisptr.Flush()
        return return_value
