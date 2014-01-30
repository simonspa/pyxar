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
        void GetInfo(string &usbId) except +
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
        void Daq_Deser400_Reset(uint8_t) except +
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
        int8_t Daq_Read_Decoded(vector[uint16_t] &, vector[uint16_t] &, vector[uint32_t] &) 
        int8_t CalibrateDacDacScan(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, vector[int16_t] &, vector[int32_t] &) 
        int8_t CalibrateDacScan(int16_t, int16_t, int16_t, int16_t, int16_t, vector[int16_t] &, vector[int32_t] &) 
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
    
    def find_dtb(self, request_id):
        cdef string dtb_id
        dtb_id = request_id
        self.thisptr.FindDTB(dtb_id)
        return dtb_id
        
    def open(self, usbId):
        try:
            return_value = self.thisptr.Open(usbId)
        except RuntimeError:
            return False
        return return_value

    def get_info(self):
        cdef string dtb_info
        self.thisptr.Init()
        self.thisptr.GetInfo(dtb_info)
        return dtb_info
    
    def cleanup(self):
        self.thisptr.Close()
    
    def flush(self):
        self.thisptr.Flush()
    
    def m_delay(self, int value):
        cdef uint16_t _value
        _value = value
        self.thisptr.mDelay(_value)
    
    def i2_c_addr(self, int identity):
        cdef uint8_t _identity
        _identity = identity
        self.thisptr.roc_I2cAddr(_identity)
    
    def set_roc_addr(self, int identity):
        cdef uint8_t _identity
        _identity = identity
        self.thisptr.SetRocAddress(_identity)
    
    def roc_set_DAC(self, int reg, int value):
        cdef uint8_t _reg
        cdef uint8_t _value
        _reg = reg
        _value = value
        self.thisptr.roc_SetDAC(_reg, _value)

    def roc_clr_cal(self):
        self.thisptr.roc_ClrCal()
        self.thisptr.Flush()
    
    def roc_chip_mask(self):
        self.thisptr.roc_Chip_Mask()
    
    def set_mod_addr(self, int identity):
        cdef uint8_t _identity
        _identity = identity
        self.thisptr.mod_Addr(_identity)

    def adjust_sig_level(self, int level):
        cdef uint8_t _level
        _level = level
        self.thisptr.Sig_SetLevel(SIG_SDA, _level)
        self.thisptr.Sig_SetLevel(SIG_CTR, _level)
        self.thisptr.Sig_SetLevel(SIG_CLK, _level)
        self.thisptr.Sig_SetLevel(SIG_TIN, _level)
    
    def tbm_set_DAC(self, int reg, int value):
        cdef uint8_t _reg
        cdef uint8_t _value
        _reg = reg
        _value = value
        self.thisptr.tbm_Set(_reg, _value)

    def tbm_enable(self, bool on):
        cdef bool _on
        _on = on
        self.thisptr.tbm_Enable(_on)

    def daq_select_deser160(self, int shift):
        cdef uint8_t _shift
        _shift = shift
        self.thisptr.Daq_Select_Deser160(_shift)
    
    def daq_select_deser400(self):
        self.thisptr.Daq_Select_Deser400()
        self.thisptr.Daq_Deser400_Reset(3)
    
    def daq_enable(self):
        self.thisptr.Daq_Open(32470, 0)
        self.thisptr.Daq_Open(32470, 1)
        self.thisptr.Daq_Start(0)
        self.thisptr.Daq_Start(1)
    
    def daq_disable(self):
        self.thisptr.Daq_Stop(0)
        self.thisptr.Daq_Stop(1)
        self.thisptr.Daq_Close(0)
        self.thisptr.Daq_Close(1)
    
    def set_mhz(self, int value):
        cdef int _value
        _value = value
        self.thisptr.SetMHz(_value)
    
    def pg_setcmd(self, addr, cmd):
        cdef uint16_t _addr
        cdef uint16_t _cmd
        _addr = addr
        _cmd = cmd
        self.thisptr.Pg_SetCmd(_addr, _cmd)
    
    def pon(self):
        self.thisptr.Pon()

    def poff(self):
        self.thisptr.Poff()
    
    def hv_on(self):
        self.thisptr.HVon()

    def hv_off(self):
        self.thisptr.HVoff()
    
    def set_id(self, int value):
        cdef uint16_t _value
        _value = value
        self.thisptr.SetID(_value)

    def set_vd(self, int value):
        cdef uint16_t _value
        _value = value
        self.thisptr.SetVD(_value)
    
    def set_ia(self, int value):
        cdef uint16_t _value
        _value = value
        self.thisptr.SetIA(_value)

    def set_va(self, int value):
        cdef uint16_t _value
        _value = value
        self.thisptr.SetVA(_value)

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
        return return_value
    
    def reset_on(self):
        self.thisptr.ResetOn()

    def reset_off(self):
        self.thisptr.ResetOff()
    
    def arm_pixel(self, col, row):
        self.thisptr.EnableColumn(col)
        self.thisptr.ArmPixel(col, row)
    
    def disarm_pixel(self, col, row):
        self.thisptr.DisarmPixel(col, row)
        
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
        cdef uint8_t return_value = self.thisptr.TrimChip(trim_bits)
        return return_value

    def calibrate(self,n_triggers, num_hits, ph, addr):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        cdef vector[uint32_t] adr
        return_value = self.thisptr.CalibrateMap_Sof(n_triggers, n_hits, ph_sum, adr)
        #return_value = self.thisptr.CalibrateMap(n_triggers, n_hits, ph_sum, adr)
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
            addr.append(adr[i]) 
        return return_value
    
    def daq_read_decoded(self, n_hits, ph, addr):
        cdef vector[uint16_t] _n_hits
        cdef vector[uint16_t] _ph
        cdef vector[uint32_t] _addr
        return_value = self.thisptr.Daq_Read_Decoded(_n_hits, _ph, _addr)
        for i in xrange(len(n_hits)):
            n_hits.append(_n_hits[i]) 
            ph.append(_ph[i]) 
            addr.append(_addr[i]) 
        return return_value

    def dac_dac(self, n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, num_hits, ph):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        #return_value = self.thisptr.CalibrateDacDacScan_Sof(n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, n_hits, ph_sum)
        return_value = self.thisptr.CalibrateDacDacScan(n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, n_hits, ph_sum)
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
        return return_value

    def dac(self, n_triggers, col, row, dac, dacRange, num_hits, ph):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        return_value = self.thisptr.CalibrateDacScan(n_triggers, col, row, dac, dacRange, n_hits, ph_sum)
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
        return return_value

    def pixel_threshold(self, n_triggers, col, row, start, step, thrLevel, dacReg, xtalk, cals, trim):
        return_value = self.thisptr.PixelThreshold(col ,row, start, step, thrLevel, n_triggers, dacReg, xtalk, cals, trim)
        return return_value
