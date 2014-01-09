// psi46_tb.cpp
#include "pixel_dtb.h"
#include <stdio.h>
#include "analyzer.h"
#ifndef _WIN32
#include <unistd.h>
#include <iostream>
#include <iomanip>
#endif

// missing defs
#define VCAL_TEST          20
int tct_wbc = 0;

bool CTestboard::EnumNext(string &name)
{
	char s[64];
	if (!usb.EnumNext(s)) return false;
	name = s;
	return true;
}

bool CTestboard::Enum(unsigned int pos, string &name)
{
	char s[64];
	if (!usb.Enum(s, pos)) return false;
	name = s;
	return true;
}


bool CTestboard::FindDTB(string &usbId)
{
	string name;
	vector<string> devList;
	unsigned int nDev;
	unsigned int nr;

	try
	{
		if (!EnumFirst(nDev)) throw int(1);
		for (nr=0; nr<nDev; nr++)
		{
			if (!EnumNext(name)) continue;
			if (name.size() < 4) continue;
			if (name.compare(0, 4, "DTB_") == 0) devList.push_back(name);
		}
	}
	catch (int e)
	{
		switch (e)
		{
		case 1: printf("Cannot access the USB driver\n"); return false;
		default: return false;
		}
	}

	if (devList.size() == 0)
	{
		printf("No DTB connected.\n");
		return false;
	}

	if (devList.size() == 1)
	{
		usbId = devList[0];
		return true;
	}

	// If more than 1 connected device list them
	printf("\nConnected DTBs:\n");
	for (nr=0; nr<devList.size(); nr++)
	{
		printf("%2u: %s", nr, devList[nr].c_str());
		if (Open(devList[nr], false))
		{
			try
			{
				unsigned int bid = GetBoardId();
				printf("  BID=%2u\n", bid);
			}
			catch (...)
			{
				printf("  Not identifiable\n");
			}
			Close();
		}
		else printf(" - in use\n");
	}

	printf("Please choose DTB (0-%u): ", (nDev-1));
	char choice[8];
	fgets(choice, 8, stdin);
	sscanf (choice, "%d", &nr);
	if (nr >= devList.size())
	{
		nr = 0;
		printf("No DTB opened\n");
		return false;
	}

	usbId = devList[nr];
	return true;
}


bool CTestboard::Open(string &usbId, bool init)
{
	rpc_Clear();
	if (!usb.Open(&(usbId[0]))) return false;

	if (init) Init();
	return true;
}


void CTestboard::Close()
{
//	if (usb.Connected()) Daq_Close();
	usb.Close();
	rpc_Clear();
}


void CTestboard::mDelay(uint16_t ms)
{
	Flush();
#ifdef _WIN32
	Sleep(ms);			// Windows
#else
	usleep(ms*1000);	// Linux
#endif
}

void CTestboard::SetMHz(int MHz = 0){
    Sig_SetDelay(SIG_CLK,  delayAdjust);
    Sig_SetDelay(SIG_SDA,  delayAdjust+15);
    Sig_SetDelay(SIG_CTR,  delayAdjust);
    Sig_SetDelay(SIG_TIN,  delayAdjust+5);
    Flush();
    tct_wbc = 5;
}

void CTestboard::prep_dig_test(){
    SetMHz();
    roc_I2cAddr(0);
    SetRocAddress(0);
}

void CTestboard::InitDAC()
{ 
    roc_SetDAC(  1,  6); // Vdig
    roc_SetDAC(  2, 132);
    roc_SetDAC(  3,  113);    // Vsf
    roc_SetDAC(  4,  12);    // Vcomp
    roc_SetDAC(  7,  60);    // VwllPr
    roc_SetDAC(  9,  60);    // VwllSh
    roc_SetDAC( 10, 230);    // VhldDel
    roc_SetDAC( 11,  29);    // Vtrim
    roc_SetDAC( 12,  20);    // VthrComp
    roc_SetDAC( 13,  1);    // VIBias_Bus
    roc_SetDAC( 14,   6);    // Vbias_sf
    roc_SetDAC( 15,  40);    // VoffsetOp
    roc_SetDAC( 17,  148);    // VoffsetRO
    roc_SetDAC( 18, 120);    // VIon
    roc_SetDAC( 19, 100);    // Vcomp_ADC
    roc_SetDAC( 20,  63);    // VIref_ADC
    roc_SetDAC( 22,  50);    // VIColOr
    roc_SetDAC( 25,   200);    // Vcal
    roc_SetDAC( 26,  107);  // CalDel
    roc_SetDAC( 0xfd, 0);   // CtrlReg
    roc_SetDAC( 0xfe,100);   // WBC

    Flush();
}

// to be renamed after kicking out psi46expert dependency
int8_t CTestboard::Daq_Enable2(int32_t block) {
	Daq_Open(block, 0);
	Daq_Open(block, 1);
    mDelay(50);
	Daq_Start(0);
	Daq_Start(1);
	return 1;
}
// to be renamed after kicking out psi46expert dependency
int8_t CTestboard::Daq_Disable2() {
	Daq_Stop(0);
	Daq_Stop(1);
    mDelay(50);
	Daq_Close(0);
	Daq_Close(1);
	return 1;
}

int8_t CTestboard::Daq_Read2(vector<uint16_t> data, uint16_t daq_read_size_2) {
	vector<uint16_t> data1;
    Daq_Read(data, daq_read_size_2,0);
    Daq_Read(data1, daq_read_size_2, 1);
    data.insert( data.end(), data1.begin(), data1.end() );
	return 1;
}

int8_t CTestboard::DecodeTbmHeader(unsigned int raw, int16_t &evNr, int16_t &stkCnt)
{
	evNr = raw >> 8;
	stkCnt = raw & 6;
    	printf("  EV(%3i) STF(%c) PKR(%c) STKCNT(%2i)",
		evNr,
		(raw&0x0080)?'1':'0',
		(raw&0x0040)?'1':'0',
		stkCnt
		); 
}

int8_t CTestboard::DecodeTbmTrailer(unsigned int raw, int16_t &dataId, int16_t &data)
{
	dataId = (raw >> 6) & 0x3;
	data   = raw & 0x3f;
    	printf("  NTP(%c) RST(%c) RSR(%c) SYE(%c) SYT(%c) CTC(%c) CAL(%c) SF(%c) D%i(%2i)",
		(raw&0x8000)?'1':'0',
		(raw&0x4000)?'1':'0',
		(raw&0x2000)?'1':'0',
		(raw&0x1000)?'1':'0',
		(raw&0x0800)?'1':'0',
		(raw&0x0400)?'1':'0',
		(raw&0x0200)?'1':'0',
		(raw&0x0100)?'1':'0',
		dataId,
		data
		);
}

int8_t CTestboard::DecodePixel(unsigned int raw, int16_t &n, int16_t &ph, int16_t &col, int16_t &row) 
{
    n = 1;
    ph = (raw & 0x0f) + ((raw >> 1) & 0xf0);
	raw >>= 9;
	int c =    (raw >> 12) & 7;
	c = c*6 + ((raw >>  9) & 7);
	int r =    (raw >>  6) & 7;
	r = r*6 + ((raw >>  3) & 7);
	r = r*6 + ( raw        & 7);
	row = 80 - r/2;
	col = 2*c + (r&1);
	printf("   Pixel [%05o] %2i/%2i: %3u", raw, col, row, ph);
	return 1;
}

int8_t CTestboard::Decode(const vector<uint16_t> &data, vector<uint16_t> &n, vector<uint16_t> &ph, vector<uint16_t> &adr)
{ 

    uint32_t words_remaining = 0;
    uint16_t hdr, trl;
	unsigned int raw;
    int16_t n_pix = 0, ph_pix = 0, col = 0, row = 0, evNr = 0, stkCnt = 0, dataId = 0, dataNr = 0;
	for (int i=0; i<data.size(); i++)
	{
		int d = data[i] & 0xf;
		int q = (data[i]>>4) & 0xf;
		switch (q)
		{
		case  0: printf("  0(%1X)", d); break;

		case  1: printf("\n R1(%1X)", d); raw = d; break;
		case  2: printf(" R2(%1X)", d);   raw = (raw<<4) + d; break;
		case  3: printf(" R3(%1X)", d);   raw = (raw<<4) + d; break;
		case  4: printf(" R4(%1X)", d);   raw = (raw<<4) + d; break;
		case  5: printf(" R5(%1X)", d);   raw = (raw<<4) + d; break;
		case  6: printf(" R6(%1X)", d);   raw = (raw<<4) + d;
			     DecodePixel(raw, n_pix, ph_pix, col, row);
				 break;

		case  7: printf("\nROC-HEADER(%1X): ", d); break;

		case  8: printf("\n\nTBM H1(%1X) ", d); hdr = d; break;
		case  9: printf("H2(%1X) ", d);       hdr = (hdr<<4) + d; break;
		case 10: printf("H3(%1X) ", d);       hdr = (hdr<<4) + d; break;
		case 11: printf("H4(%1X) ", d);       hdr = (hdr<<4) + d; 
			     DecodeTbmHeader(hdr, evNr, stkCnt);
			     break;

		case 12: printf("\nTBM T1(%1X) ", d); trl = d; break;
		case 13: printf("T2(%1X) ", d);       trl = (trl<<4) + d; break;
		case 14: printf("T3(%1X) ", d);       trl = (trl<<4) + d; break;
		case 15: printf("T4(%1X) ", d);       trl = (trl<<4) + d;
			     DecodeTbmTrailer(trl, dataId, dataNr);
			     break;
		}
	}
}

int8_t CTestboard::CalibrateMap_Sof(int16_t nTriggers, vector<int16_t> &nReadouts, vector<int32_t> &PHsum)
{
    /*uint16_t daq_read_size = 32768;
	int16_t pos = 0;
	int16_t ok = -1;
	vector<uint16_t> n, ph, adr;

	Daq_Enable2(daq_read_size);
	vector<uint16_t> data;

	for (uint8_t col = 0; col < ROC_NUMCOLS; col++) {
		roc_Col_Enable(col, true);
		for (uint8_t row = 0; row < ROC_NUMROWS; row++) {
			//arm
			roc_Pix_Cal(col, row, false);
			uDelay(5);
			for (uint8_t trigger = 0; trigger < nTriggers; trigger++) {
				//send triggers
				Pg_Single();
				uDelay(4);
			}
			// clear
			roc_ClrCal();
		}

		//read data
		data.clear();
		Daq_Read2(data, daq_read_size);
        DumpData(data, 200);
		pos = 0;
		for (uint8_t row = 0; row < ROC_NUMROWS; row++) {
			//decode n readouts
			for (int8_t trigger = 0; trigger < nTriggers; trigger++) {
				ok = Decode(data, n, ph, adr);
				if (ok) {
					nReadouts.insert(nReadouts.end(), n.begin(), n.end());
					PHsum.insert(PHsum.end(), ph.begin(), ph.end());
				}
			}
		}

		roc_Col_Enable(col, false);
	}

	Daq_Disable2();*/
    int col = 5, row = 5;
    Daq_Select_Deser400();
	mDelay(10);
    Daq_Deser400_Reset(3);
	mDelay(10);

    for (int i=0;    i<16;      i++) {
    roc_I2cAddr(i);
	mDelay(50);
    roc_Col_Enable(col, true);
    roc_Pix_Trim(col, row, 15);
	roc_Pix_Cal(col, row, false);
	mDelay(50);
    }

    Daq_Open(1000,0);
    Daq_Open(1000,1);
	mDelay(50);
    Daq_Start(0);
    Daq_Start(1);

    PixelReadoutData pix;
    uint32_t n = 0;
    uint8_t status;
	mDelay(50);

    for (int16_t l=0; l < nTriggers; l++)
    {
                Pg_Single();
	            mDelay(100);
    }
    for (int i =0;    i<16;      i++) roc_ClrCal();
	mDelay(100);
    vector<uint16_t> data;
    vector<uint16_t> data1;
    status = Daq_Read(data, 4096, n, 0);
	mDelay(50);
    status = Daq_Read(data1, 4096, n, 1);
	mDelay(50);
    //data.insert( data.end(), data1.begin(), data1.end() );
    int pos = 0;
    int pos1 = 0;
    int32_t nHits = 0;
    vector<uint16_t> nhits, ph, adr;
    DumpData(data, 200);
    DumpData(data1, 200);
	mDelay(50);
    try
    {
                for (int16_t l=0; l < nTriggers; l++)
                {
                    DecodePixelW(data, pos, pix);
                    Decode(data, nhits, ph, adr);
                    Decode(data1, nhits, ph, adr);
                    if (pix.n > 0) nHits++;
                }
    } catch (int) {}
    cout << "hits:" << nHits++ << endl;
    Daq_Stop(0);
    Daq_Stop(1);
    Daq_Close(0);
    Daq_Close(1);
    return 1;
}

void CTestboard::ArmPixel(int col, int row)
{
	ArmPixel(col, row, 15);
}


void CTestboard::ArmPixel(int col, int row, int trim)
{
	roc_Pix_Trim(col, row, trim);
	roc_Pix_Cal(col, row, false);
}


void CTestboard::EnableColumn(int col)
{
		roc_Col_Enable(col, 1);
		cDelay(20);
}


void CTestboard::EnableAllPixels(int32_t trim[])
{
	for (int col = 0; col < ROC_NUMCOLS; col++)
	{
		EnableColumn(col);
		for (int row = 0; row < ROC_NUMROWS; row++)
		{
			roc_Pix_Trim(col, row, trim[col*ROC_NUMROWS + row]);
		}
	}
}
	
	
void CTestboard::DisableAllPixels()
{
    roc_Chip_Mask();
}


void CTestboard::DisarmPixel(int col, int row)
{
	roc_ClrCal();
	roc_Pix_Mask(col,row);
}

void CTestboard::SetHubID(int32_t value)
{
    hubId = value;
}


void CTestboard::SetNRocs(int32_t value)
{
    nRocs = value;
}

void CTestboard::SetChip(int iChip)
{
	int portId = iChip/4;
	//tbm_Addr(hubId, portId);
	roc_I2cAddr(iChip);
    SetRocAddress(iChip);
}

// == Thresholds ===================================================


void CTestboard::ChipThresholdIntern(int32_t start[], int32_t step, int32_t thrLevel, int32_t nTrig, int32_t dacReg, int32_t xtalk, int32_t cals, int32_t trim[], int32_t res[])
{
  int32_t thr, startValue;
	for (int col = 0; col < ROC_NUMCOLS; col++)
	{
		EnableColumn(col);
		for (int row = 0; row < ROC_NUMROWS; row++)
		{
			if (step < 0) startValue = start[col*ROC_NUMROWS + row] + 10;
			else startValue = start[col*ROC_NUMROWS + row];
			if (startValue < 0) startValue = 0;
			else if (startValue > 255) startValue = 255;
			
			thr = PixelThreshold(col, row, startValue, step, thrLevel, nTrig, dacReg, xtalk, cals, trim[col*ROC_NUMROWS + row]);
			res[col*ROC_NUMROWS + row] = thr;
		}
		roc_Col_Enable(col, 0);
	}
}

void CTestboard::Init_Reset()
{
    prep_dig_test();
    InitDAC();
    roc_Chip_Mask();

    Pg_SetCmd(0, PG_RESR + 25);
    Pg_SetCmd(1, PG_CAL  + 101 + tct_wbc);
    Pg_SetCmd(2, PG_TRG  + 16);
    Pg_SetCmd(3, PG_TOK);
    uDelay(100);
    Flush();
}

void CTestboard::Init_PG()
{
    Pg_SetCmd(0, PG_RESR + 25);
    Pg_SetCmd(1, PG_CAL  + 100 + tct_wbc);
    Pg_SetCmd(2, PG_SYNC + PG_TRG);
    Pg_SetCmd(3, PG_CAL  + 100 + tct_wbc);
    Pg_SetCmd(4, PG_TRG  + 16);
    Pg_SetCmd(5, PG_CAL  + 100 + tct_wbc);
    Pg_SetCmd(6, PG_TRG  );
    //Pg_SetCmd(3, PG_TOK);
    uDelay(100);
    Flush();
}

int32_t CTestboard::ChipThreshold(int32_t start, int32_t step, int32_t thrLevel, int32_t nTrig, int32_t dacReg, int32_t xtalk, int32_t cals, int32_t trim[], int32_t res[])
{
  int startValue;
  int32_t roughThr[ROC_NUMROWS * ROC_NUMCOLS], roughStep;
  if (step < 0) 
  {
  	startValue = 255;
  	roughStep = -4;
  }
  else 
  {
  	startValue = 0;
  	roughStep = 4;
  }
  
  for (int i = 0; i < ROC_NUMROWS * ROC_NUMCOLS; i++) roughThr[i] = startValue;
  ChipThresholdIntern(roughThr, roughStep, 0, 1, dacReg, xtalk, cals, trim, roughThr);
  ChipThresholdIntern(roughThr, step, thrLevel, nTrig, dacReg, xtalk, cals, trim, res);  
  return 1;
}
