from libcpp cimport bool
from libcpp.vector cimport vector
from libc.stdint cimport uint8_t, int8_t, uint16_t, int16_t, int32_t
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
        void Init_PG() except +
        void roc_I2cAddr(uint8_t) except +
        void SetRocAddress(uint8_t) except +
        void roc_SetDAC(uint8_t, uint8_t) except +
        void roc_ClrCal() except +
        void roc_Chip_Mask() except +
        void Daq_Select_Deser160(uint8_t shift) except +
        void EnableColumn(int) except +
        void ArmPixel(int, int) except +
        void DisarmPixel(int, int) except +
        int8_t CalibrateDacDacScan(int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, int16_t, vector[int16_t] &, vector[int32_t] &) 
        int8_t CalibrateMap(int16_t, vector[int16_t] &, vector[int32_t] &) 
        int8_t TrimChip(vector[int8_t] &) 
        int32_t MaskTest(int16_t, int16_t*) 
        int32_t ChipThreshold(int32_t, int32_t, int32_t, int32_t, int32_t, int32_t, int32_t, int32_t *, int32_t *)


cdef class PyDTB: 
    cdef CTestboard *thisptr
    def __cinit__(self): 
        self.thisptr = new CTestboard()

    def __dealloc__(self): 
        del self.thisptr
    
    def find_dtb(self,usbId):
        return  self.thisptr.FindDTB(usbId)
        
    def open(self,usbId):
        self.thisptr.Open(usbId)
        self.thisptr.Flush()
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
    
    def i2_c_addr(self,identity):
        self.thisptr.roc_I2cAddr(identity)
    
    def set_roc_addr(self, identity):
        self.thisptr.SetRocAddress(identity)
    
    def roc_set_DAC(self, reg, value):
        self.thisptr.roc_SetDAC(reg, value)

    def roc_clr_cal(self):
        self.thisptr.roc_ClrCal()
        self.thisptr.Flush()
    
    def roc_chip_mask(self):
        self.thisptr.roc_Chip_Mask()
        self.thisptr.Flush()
    
    def daq_select_deser160(self, shift):
        self.thisptr.Daq_Select_Deser160(shift)
        self.thisptr.Flush()
    
    def set_mhz(self, value):
        self.thisptr.SetMHz(value)
        self.thisptr.Flush()
    
    def init_pg(self):
        self.thisptr.Init_PG()
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
        return self.thisptr.GetIA()*1000.
    
    def get_id(self):
        return self.thisptr.GetID()*1000.
    
    def get_va(self):
        return self.thisptr.GetVA()
    
    def get_vd(self):
        return self.thisptr.GetVD()
    
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
        for i in xrange(n):
            result[i] = data[i] 
        free(data)
        free(trim_bits)
        return return_value
    
    def trim_chip(self, trim):
        cdef vector[int8_t] trim_bits
        for i in xrange(len(trim_bits)):
            trim_bits[i] = trim[i]
        return self.thisptr.TrimChip(trim_bits)

    def calibrate(self,n_triggers, num_hits, ph):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        return_value = self.thisptr.CalibrateMap(n_triggers, n_hits, ph_sum)
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
        return return_value

    def dac_dac(self, n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, num_hits, ph):
        cdef vector[int16_t] n_hits
        cdef vector[int32_t] ph_sum
        return_value = self.thisptr.CalibrateDacDacScan(n_triggers, col, row, dac1, dacRange1, dac2, dacRange2, n_hits, ph_sum)
        for i in xrange(len(n_hits)):
            num_hits.append(n_hits[i]) 
            ph.append(ph_sum[i]) 
        return return_value
