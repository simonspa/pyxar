from libcpp cimport bool
from libc.stdint cimport uint8_t, int16_t, int32_t
from libc.stdlib cimport malloc, free

cdef extern from "string" namespace "std":
    cdef cppclass string:
        char* c_str()


cdef extern from "pixel_dtb.h":
    cdef cppclass CTestboard:
        CTestboard()
        bool FindDTB(string &usbId)
        bool Open(string &usbId)
        void Close()
        void Welcome()
        void Flush()
        void Init()
        void Pon()
        void Poff()
        void HVon()
        void HVoff()
        void ResetOn()
        void ResetOff()
        void SetVA(double)
        void SetVD(double)
        void SetIA(double)
        void SetID(double)
        void Init_Reset()
        void prep_dig_test()
        void DisableAllPixels()
        void SetChip(int)
        void SetMHz(int)
        void InitDAC()
        void roc_I2cAddr(uint8_t)
        void Daq_Select_Deser160(uint8_t shift)
        void EnableColumn(int)
        void ArmPixel(int, int)
        void DisarmPixel(int, int)
        int32_t MaskTest(int16_t, int16_t*)
        int32_t ChipEfficiency(int16_t, int32_t*, double*)
        void DacDac(int32_t, int32_t, int32_t, int32_t, int32_t, int32_t *)


cdef class PyDTB: 
    cdef CTestboard *thisptr
    def __cinit__(self): 
        self.thisptr = new CTestboard()

    def __dealloc__(self): 
        del self.thisptr
    
    def find_dtb(self,usbId):
        return self.thisptr.FindDTB(usbId)
        
    def open(self,usbId):
        self.thisptr.Open(usbId)
        self.thisptr.Flush()
        self.thisptr.Welcome()
        self.thisptr.Flush()
        self.thisptr.Init()
        self.thisptr.Flush()
        return True
    
    def cleanup(self):
        self.thisptr.Close()
    
    def flush(self):
        self.thisptr.Flush()
    
    def i2_c_addr(self,identity):
        self.thisptr.roc_I2cAddr(identity)
    
    def daq_select_deser160(self, shift):
        self.thisptr.Daq_Select_Deser160(shift)
    
    def prep_dig_test(self):
        self.thisptr.prep_dig_test()
        self.thisptr.InitDAC()

    def set_chip(self, value):
        self.thisptr.SetChip(value)
    
    def set_mhz(self, value):
        self.thisptr.SetMHz(value)
    
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

    def set_vd(self, value):
        self.thisptr.SetVD(value)
    
    def set_ia(self, value):
        self.thisptr.SetIA(value)

    def set_va(self, value):
        self.thisptr.SetVA(value)

    def reset_on(self):
        self.thisptr.ResetOn()
        self.thisptr.Flush()

    def reset_off(self):
        self.thisptr.ResetOff()
        self.thisptr.Flush()
    
    def init_roc(self):
        self.thisptr.Init_Reset()
    
    def arm_pixel(self, col, row):
        self.thisptr.EnableColumn(col)
        self.thisptr.ArmPixel(col, row)
        self.thisptr.Flush()
    
    def disarm_pixel(self, col, row):
        self.thisptr.DisarmPixel(col, row)
        self.thisptr.Flush()
        
    def mask_test(self,n_triggers, result):
        cdef int16_t *data
        n = len(result) 
        data = <int16_t *>malloc(n*sizeof(int))
        return_value = self.thisptr.MaskTest(n_triggers, data)
        for i in range(n):
            result[i] = data[i] 
        free(data)
        return return_value
    
    def chip_efficiency(self,n_triggers, trim, result):
        cdef double *data
        cdef int32_t *trim_bits
        n = len(result) 
        n_trim = len(trim) 
        data = <double *>malloc(n*sizeof(double))
        trim_bits = <int32_t *>malloc(n_trim*sizeof(int))
        for i in xrange(n_trim):
            trim_bits[i] = trim[i]
        return_value = self.thisptr.ChipEfficiency(n_triggers, trim_bits, data)
        for i in xrange(n):
            result[i] = data[i] 
        free(data)
        free(trim_bits)
        return return_value
    
    def dac_dac(self, dac1, dacRange1, dac2, dacRange2, n_triggers, result):
        cdef int32_t *data
        n = len(result) 
        data = <int32_t *>malloc(n*sizeof(int))
        self.thisptr.DacDac(dac1, dacRange1, dac2, dacRange2, n_triggers, data)
        for i in xrange(n):
            result[i] = data[i] 
        free(data)
