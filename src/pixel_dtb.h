/*---------------------------------------------------------------------
 *
 *  filename:    pixel_dtb.h
 *
 *  description: PSI46 testboard API for DTB
 *	author:      Beat Meier
 *	date:        15.7.2013
 *	rev:
 *
 *---------------------------------------------------------------------
 */


// ---------------------------------------------------
#define TITLE        "PSI46V2 ROC/Wafer Tester"
#define PIXEL_DTB_VERSION      "V1.3"
#define TIMESTAMP    "07.08.2013"
// ---------------------------------------------------

#define VERSIONINFO TITLE " " PIXEL_DTB_VERSION " (" TIMESTAMP ")"


#pragma once

// #define RPC_MULTITHREADING
#include "rpc.h"

#ifdef _WIN32
#include "pipe.h"
#endif

#include "USBInterface.h"

// size of ROC pixel array
#define ROC_NUMROWS  80  // # rows
#define ROC_NUMCOLS  52  // # columns
#define ROC_NUMDCOLS 26  // # double columns (= columns/2)
#define ROC_NUMDCOLS 26  // # double columns (= columns/2)


#define PIXMASK  0x80

// PUC register addresses for roc_SetDAC
#define	Vdig        0x01
#define Vana        0x02
#define	Vsh         0x03
#define	Vcomp       0x04
#define	Vleak_comp  0x05
#define	VrgPr       0x06
#define	VwllPr      0x07
#define	VrgSh       0x08
#define	VwllSh      0x09
#define	VhldDel     0x0A
#define	Vtrim       0x0B
#define	VthrComp    0x0C
#define	VIBias_Bus  0x0D
#define	Vbias_sf    0x0E
#define	VoffsetOp   0x0F
#define	VIbiasOp    0x10
#define	VoffsetRO   0x11
#define	VIon        0x12
#define	VIbias_PH   0x13
#define	Ibias_DAC   0x14
#define	VIbias_roc  0x15
#define	VIColOr     0x16
#define	Vnpix       0x17
#define	VsumCol     0x18
#define	Vcal        0x19
#define	CalDel      0x1A
#define	RangeTemp   0x1B
#define	WBC         0xFE
#define	CtrlReg     0xFD




class CTestboard
{
	RPC_DEFS
	RPC_THREAD

#ifdef _WIN32
	CPipeClient pipe;
#endif
	CUSB usb;

public:
	CRpcIo& GetIo() { return *rpc_io; }

	CTestboard() { RPC_INIT rpc_io = &usb;
	  // Set defaults for deser160 variables:
	  delayAdjust = 4;
	  deserAdjust = 4;
	}
	~CTestboard() { RPC_EXIT }

	//FIXME not nice but better than global variables:
	int delayAdjust;
	int deserAdjust;

	// === RPC ==============================================================

	// Don't change the following two entries
	RPC_EXPORT uint16_t GetRpcVersion();
	RPC_EXPORT int32_t  GetRpcCallId(string &callName);

	RPC_EXPORT void GetRpcTimestamp(stringR &ts);

	RPC_EXPORT int32_t GetRpcCallCount();
	RPC_EXPORT bool    GetRpcCallName(int32_t id, stringR &callName);

	// === DTB connection ====================================================

	bool EnumFirst(unsigned int &nDevices) { return usb.EnumFirst(nDevices); };
	bool EnumNext(string &name);
	bool Enum(unsigned int pos, string &name);

	bool FindDTB(string &usbId);
	bool Open(string &name, bool init=true); // opens a connection
	void Close();				// closes the connection to the testboard

#ifdef _WIN32
	bool OpenPipe(const char *name) { return pipe.Open(name); }
	void ClosePipe() { pipe.Close(); }
#endif

	void SetTimeout(unsigned int timeout) { usb.SetTimeout(timeout); }

	bool IsConnected() { return usb.Connected(); }
	const char * ConnectionError()
	{ return usb.GetErrorMsg(usb.GetLastError()); }

	void Flush() { rpc_io->Flush(); }
	void Clear() { rpc_io->Clear(); }


	// === DTB identification ================================================

	RPC_EXPORT void GetInfo(stringR &info);
	RPC_EXPORT uint16_t GetBoardId();
	RPC_EXPORT void GetHWVersion(stringR &version);
	RPC_EXPORT uint16_t GetFWVersion();
	RPC_EXPORT uint16_t GetSWVersion();


	// === DTB service ======================================================

	// --- upgrade
	RPC_EXPORT uint16_t UpgradeGetVersion();
	RPC_EXPORT uint8_t  UpgradeStart(uint16_t version);
	RPC_EXPORT uint8_t  UpgradeData(string &record);
	RPC_EXPORT uint8_t  UpgradeError();
	RPC_EXPORT void     UpgradeErrorMsg(stringR &msg);
	RPC_EXPORT void     UpgradeExec(uint16_t recordCount);


	// === DTB functions ====================================================

	RPC_EXPORT void Init();

	RPC_EXPORT void Welcome();
	RPC_EXPORT void SetLed(uint8_t x);


	// --- Clock, Timing ----------------------------------------------------
	RPC_EXPORT void cDelay(uint16_t clocks);
	RPC_EXPORT void uDelay(uint16_t us);
	void mDelay(uint16_t ms);


	// --- Signal Delay -----------------------------------------------------
	#define SIG_CLK 0
	#define SIG_CTR 1
	#define SIG_SDA 2
	#define SIG_TIN 3

	#define SIG_MODE_NORMAL  0
	#define SIG_MODE_LO      1
	#define SIG_MODE_HI      2

	RPC_EXPORT void Sig_SetMode(uint8_t signal, uint8_t mode);
	RPC_EXPORT void Sig_SetPRBS(uint8_t signal, uint8_t speed);
	RPC_EXPORT void Sig_SetDelay(uint8_t signal, uint16_t delay, int8_t duty = 0);
	RPC_EXPORT void Sig_SetLevel(uint8_t signal, uint8_t level);
	RPC_EXPORT void Sig_SetOffset(uint8_t offset);
	RPC_EXPORT void Sig_SetLVDS();
	RPC_EXPORT void Sig_SetLCDS();


	// --- digital signal probe ---------------------------------------------
	#define PROBE_OFF     0
	#define PROBE_CLK     1
	#define PROBE_SDA     2
	#define PROBE_PGTOK   3
	#define PROBE_PGTRG   4
	#define PROBE_PGCAL   5
	#define PROBE_PGRESR  6
	#define PROBE_PGREST  7
	#define PROBE_PGSYNC  8
	#define PROBE_CTR     9
	#define PROBE_CLKP   10
	#define PROBE_CLKG   11
	#define PROBE_CRC    12

	RPC_EXPORT void SignalProbeD1(uint8_t signal);
	RPC_EXPORT void SignalProbeD2(uint8_t signal);


	// --- analog signal probe ----------------------------------------------
	#define PROBEA_TIN     0
	#define PROBEA_SDATA1  1
	#define PROBEA_SDATA2  2
	#define PROBEA_CTR     3
	#define PROBEA_CLK     4
	#define PROBEA_SDA     5
	#define PROBEA_TOUT    6
	#define PROBEA_OFF     7

	#define GAIN_1   0
	#define GAIN_2   1
	#define GAIN_3   2
	#define GAIN_4   3

	RPC_EXPORT void SignalProbeA1(uint8_t signal);
	RPC_EXPORT void SignalProbeA2(uint8_t signal);
	RPC_EXPORT void SignalProbeADC(uint8_t signal, uint8_t gain = 0);


	// --- ROC/Module power VD/VA -------------------------------------------
	RPC_EXPORT void Pon();	// switch ROC power on
	RPC_EXPORT void Poff();	// switch ROC power off

	RPC_EXPORT void _SetVD(uint16_t mV);
	RPC_EXPORT void _SetVA(uint16_t mV);
	RPC_EXPORT void _SetID(uint16_t uA100);
	RPC_EXPORT void _SetIA(uint16_t uA100);

	RPC_EXPORT uint16_t _GetVD();
	RPC_EXPORT uint16_t _GetVA();
	RPC_EXPORT uint16_t _GetID();
	RPC_EXPORT uint16_t _GetIA();

	void SetVA(double V) { _SetVA(uint16_t(V*1000)); }  // set VA voltage
	void SetVD(double V) { _SetVD(uint16_t(V*1000)); }  // set VD voltage
	void SetIA(double A) { _SetIA(uint16_t(A*10000)); }  // set VA current limit
	void SetID(double A) { _SetID(uint16_t(A*10000)); }  // set VD current limit

	double GetVA() { return _GetVA()/1000.0; }   // get VA voltage in V
	double GetVD() { return _GetVD()/1000.0; }	 // get VD voltage in V
	double GetIA() { return _GetIA()/10000.0; }  // get VA current in A
	double GetID() { return _GetID()/10000.0; }  // get VD current in A

	RPC_EXPORT void HVon();
	RPC_EXPORT void HVoff();
	RPC_EXPORT void ResetOn();
	RPC_EXPORT void ResetOff();
	RPC_EXPORT uint8_t GetStatus();
	RPC_EXPORT void SetRocAddress(uint8_t addr);


	// --- pulse pattern generator ------------------------------------------
	#define PG_TOK   0x0100
	#define PG_TRG   0x0200
	#define PG_CAL   0x0400
	#define PG_RESR  0x0800
	#define PG_REST  0x1000
	#define PG_SYNC  0x2000

	RPC_EXPORT void Pg_SetCmd(uint16_t addr, uint16_t cmd);
//	RPC_EXPORT void Pg_SetCmdAll(vector<uint16_t> &cmd);
	RPC_EXPORT void Pg_Stop();
	RPC_EXPORT void Pg_Single();
	RPC_EXPORT void Pg_Trigger();
	RPC_EXPORT void Pg_Loop(uint16_t period);

	RPC_EXPORT uint16_t GetUser1Version();


	// --- data aquisition --------------------------------------------------
    RPC_EXPORT uint32_t Daq_Open(uint32_t buffersize = 10000000, uint8_t channel = 0);
	RPC_EXPORT void Daq_Close(uint8_t channel = 0);
	RPC_EXPORT void Daq_Start(uint8_t channel = 0);
	RPC_EXPORT void Daq_Stop(uint8_t channel = 0);
	RPC_EXPORT uint32_t Daq_GetSize(uint8_t channel = 0);

	RPC_EXPORT uint8_t Daq_Read(vectorR<uint16_t> &data,
			 uint16_t blocksize = 16384, uint8_t channel = 0);

	RPC_EXPORT uint8_t Daq_Read(vectorR<uint16_t> &data,
			uint16_t blocksize, uint32_t &availsize, uint8_t channel = 0);


	RPC_EXPORT void Daq_Select_ADC(uint16_t blocksize, uint8_t source,
			uint8_t start, uint8_t stop = 0);

	RPC_EXPORT void Daq_Select_Deser160(uint8_t shift);

	RPC_EXPORT void Daq_Select_Deser400();
	RPC_EXPORT void Daq_Deser400_Reset(uint8_t reset = 3);

	RPC_EXPORT void Daq_DeselectAll();

	// --- ROC/module Communication -----------------------------------------
	// -- set the i2c address for the following commands
	RPC_EXPORT void roc_I2cAddr(uint8_t id);

	// -- sends "ClrCal" command to ROC
	RPC_EXPORT void roc_ClrCal();

	// -- sets a single (DAC) register
	RPC_EXPORT void roc_SetDAC(uint8_t reg, uint8_t value);

	// -- set pixel bits (count <= 60)
	//    M - - - 8 4 2 1
	RPC_EXPORT void roc_Pix(uint8_t col, uint8_t row, uint8_t value);

	// -- trimm a single pixel (count < =60)
	RPC_EXPORT void roc_Pix_Trim(uint8_t col, uint8_t row, uint8_t value);

	// -- mask a single pixel (count <= 60)
	RPC_EXPORT void roc_Pix_Mask(uint8_t col, uint8_t row);

	// -- set calibrate at specific column and row
	RPC_EXPORT void roc_Pix_Cal(uint8_t col, uint8_t row, bool sensor_cal = false);

	// -- enable/disable a double column
	RPC_EXPORT void roc_Col_Enable(uint8_t col, bool on);

	// -- mask all pixels of a column and the coresponding double column
	RPC_EXPORT void roc_Col_Mask(uint8_t col);

	// -- mask all pixels and columns of the chip
	RPC_EXPORT void roc_Chip_Mask();
    // == TBM functions =====================================================
    RPC_EXPORT bool TBM_Present(); 

    RPC_EXPORT void tbm_Enable(bool on);

    RPC_EXPORT void tbm_Addr(uint8_t hub, uint8_t port);

    RPC_EXPORT void mod_Addr(uint8_t hub);

    RPC_EXPORT void tbm_Set(uint8_t reg, uint8_t value);

    RPC_EXPORT bool tbm_Get(uint8_t reg, uint8_t &value);

    RPC_EXPORT bool tbm_GetRaw(uint8_t reg, uint32_t &value);


// --- Wafer test functions
	RPC_EXPORT bool TestColPixel(uint8_t col, uint8_t trimbit, vectorR<uint8_t> &res);

	// Ethernet test functions
	RPC_EXPORT void Ethernet_Send(string &message);
	RPC_EXPORT uint32_t Ethernet_RecvPackets();


    RPC_EXPORT int8_t CalibratePixel(int16_t nTriggers, int16_t col, int16_t row, int16_t &nReadouts, int32_t &PHsum);
	RPC_EXPORT int8_t CalibrateDacScan(int16_t nTriggers, int16_t col, int16_t row, int16_t dacReg1, int16_t dacLower1, int16_t dacUpper1, vectorR<int16_t> &nReadouts, vectorR<int32_t> &PHsum);
    RPC_EXPORT int8_t CalibrateDacDacScan(int16_t nTriggers, int16_t col, int16_t row, int16_t dacReg1, int16_t dacLower1, int16_t dacUpper1, int16_t dacReg2, int16_t dacLower2, int16_t dacUpper2, vectorR<int16_t> &nReadouts, vectorR<int32_t> &PHsum);
    RPC_EXPORT int16_t CalibrateMap(int16_t nTriggers, vectorR<int16_t> &nReadouts, vectorR<int32_t> &totalPH, vector<uint32_t> &address);
    RPC_EXPORT int16_t TrimChip(vector<int16_t> &);
    int8_t TrimChip_Sof(vector<int16_t> &);
    //int8_t TrimChip_Sof(int16_t trim[]);

    RPC_EXPORT bool GetPixelAddressInverted();

    RPC_EXPORT void SetClockSource(uint8_t source);

    // === module test functions ======================================
    
    // --- implemented funtions: ---
    void InitDAC();
    void Init_Reset();
    void Init_PG();
    void prep_dig_test();
    void SetMHz(int MHz);
    void I2cAddr(unsigned char id){ roc_I2cAddr(id); }
    void Set(unsigned char reg, unsigned char value){ roc_SetDAC(reg, value); }
    void SetReg(unsigned char addr, uint16_t value){ roc_SetDAC(addr, value); }
    void ArmPixel(int col, int row);
    void ArmPixel(int col, int row, int trim);    
    void DisarmPixel(int col, int row);
    void DisableAllPixels();
    void EnableColumn(int col);
    void EnableAllPixels(int32_t trim[]);
    void SetChip(int iChip);    
	void Ping(int32_t, int32_t, int32_t);
    RPC_EXPORT int32_t CountReadouts(int32_t nTriggers);
	RPC_EXPORT int32_t CountReadouts(int32_t nTriggers, int32_t chipId);
	RPC_EXPORT int32_t CountReadouts(int32_t nTriggers, int32_t dacReg, int32_t dacValue);
	RPC_EXPORT int32_t PixelThreshold(int32_t col, int32_t row, int32_t start, int32_t step, int32_t thrLevel, int32_t nTrig, int32_t dacReg, bool xtalk, bool cals, int32_t trim);
	int32_t ChipThreshold(int32_t start, int32_t step, int32_t thrLevel, int32_t nTrig, int32_t dacReg, int32_t xtalk, int32_t cals, int32_t trim[], int32_t res[]);
	void ChipThresholdIntern(int32_t start[], int32_t step, int32_t thrLevel, int32_t nTrig, int32_t dacReg, int32_t xtalk, int32_t cals, int32_t trim[], int32_t res[]);
    RPC_EXPORT int32_t PH(int32_t col, int32_t row, int32_t trim, int16_t nTriggers);
    RPC_EXPORT bool test_pixel_address(int32_t col, int32_t row);
    RPC_EXPORT int32_t ChipEfficiency_dtb(int16_t nTriggers, vectorR<uint8_t> &res);
    RPC_EXPORT int8_t ThresholdMap(int32_t nTriggers, int32_t dacReg, bool rising, bool xtalk, bool cals, vectorR<int16_t> &thrValue);
    void SetNRocs(int32_t value);
    void SetHubID(int32_t value);

    int8_t Daq_Enable2(int32_t block);
    int8_t Daq_Read2(vector<uint16_t> &data, uint16_t daq_read_size, uint32_t &n, uint8_t channel);
    int8_t Daq_Disable2();
    int8_t CalibrateReadouts(int16_t nTriggers, int16_t &nReadouts, int32_t &PHsum);
    int8_t CalibrateMap_Sof(int16_t nTriggers, vector<int16_t> &nReadouts, vector<int32_t> &PHsum, vector<uint32_t> &addres);
    int8_t CalibrateMap_Par(int16_t nTriggers, vector<int16_t> &nReadouts, vector<int32_t> &PHsum, vector<uint32_t> &addres, int16_t nRocs);
    int8_t CalibrateDacDacScan_Sof(int16_t nTriggers, int16_t col, int16_t row, int16_t dacReg1, int16_t dacLower1, int16_t dacUpper1, int16_t dacReg2, int16_t dacLower2, int16_t dacUpper2, vector<int16_t> &nReadouts, vector<int32_t> &PHsum);
    int8_t Daq_Read_Decoded(vector<uint16_t> &nReadouts, vector<uint16_t> &PHsum, vector<uint32_t> &adress);
    

    RPC_EXPORT int16_t TriggerRow(int16_t nTriggers, int16_t col, int16_t nRocs, int16_t delay=4);

    // new spannagel stuff
    RPC_EXPORT uint32_t GetRpcCallHash();
    RPC_EXPORT bool IsClockPresent();
    RPC_EXPORT void SetClock(uint8_t);
    RPC_EXPORT void SetClockStretch(uint8_t, uint16_t, uint16_t);
    RPC_EXPORT void SetPixelAddressInverted(bool);

    // ----------------------------

private:
    int hubId;
    int nRocs;
    
};
