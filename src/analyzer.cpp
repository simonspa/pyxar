// analyzer.cpp

#include "analyzer.h"

using namespace std;


void DumpData(const vector<uint16_t> &x, unsigned int n)
{
	unsigned int i;
	printf("\n%i samples\n", int(x.size()));
	for (i=0; i<n && i<x.size(); i++)
	{
		if (x[i] & 0x8000) printf(">"); else printf(" ");
		printf("%03X", (unsigned int)(x[i] & 0xfff));
		if (i%16 == 15) printf("\n");
	}
	printf("\n");
}



void DecodeTbmHeader(unsigned int raw, int16_t &evNr, int16_t &stkCnt)
{
  evNr = raw >> 8;
  stkCnt = raw & 6;
  /* printf(" EV(%3i) STF(%c) PKR(%c) STKCNT(%2i)",
evNr,
(raw&0x0080)?'1':'0',
(raw&0x0040)?'1':'0',
stkCnt
); */
     }

void DecodeTbmTrailer(unsigned int raw, int16_t &dataId, int16_t &data)
{
  dataId = (raw >> 6) & 0x3;
  data = raw & 0x3f;
  /* printf(" NTP(%c) RST(%c) RSR(%c) SYE(%c) SYT(%c) CTC(%c) CAL(%c) SF(%c) D%i(%2i)",
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
);*/
}

void DecodePixel(unsigned int raw, int16_t &n, int16_t &ph, int16_t &col, int16_t &row)
{
  n = 1;
  ph = (raw & 0x0f) + ((raw >> 1) & 0xf0);
  raw >>= 9;
  int c = (raw >> 12) & 7;
  c = c*6 + ((raw >> 9) & 7);
  int r = (raw >> 6) & 7;
  r = r*6 + ((raw >> 3) & 7);
  r = r*6 + ( raw & 7);
  row = 80 - r/2;
  col = 2*c + (r&1);
  //printf(" Pixel [%05o] %2i/%2i: %3u", raw, col, row, ph);
}

int8_t Decode(const std::vector<uint16_t> &data, std::vector<uint16_t> &n, std::vector<uint16_t> &ph, std::vector<uint32_t> &adr, uint8_t channel, bool has_tbm)
{

  uint32_t words_remaining = 0;
  uint16_t hdr, trl;
  unsigned int raw;
  int16_t n_pix = 0, ph_pix = 0, col = 0, row = 0, evNr = 0, stkCnt = 0, dataId = 0, dataNr = 0;
  int16_t roc_n = -1;
  int16_t tbm_n = 0;
  uint32_t address;
  int pos = 0;
  //Module readout
  if (has_tbm){
    for (int i=0; i<data.size(); i++)
      {
	int d = data[i] & 0xf;
	int q = (data[i]>>4) & 0xf;
	switch (q)
	  {
	  case 0: break;

	  case 1: raw = d; break;
	  case 2: raw = (raw<<4) + d; break;
	  case 3: raw = (raw<<4) + d; break;
	  case 4: raw = (raw<<4) + d; break;
	  case 5: raw = (raw<<4) + d; break;
	  case 6: raw = (raw<<4) + d;
	    DecodePixel(raw, n_pix, ph_pix, col, row);
	    n.push_back(n_pix);
	    ph.push_back(ph_pix);
	    address = channel;
	    address = (address << 8) + roc_n;
	    address = (address << 8) + col;
	    address = (address << 8) + row;
	    adr.push_back(address);
	    break;

	  case 7: roc_n++; break;

	  case 8: hdr = d; break;
	  case 9: hdr = (hdr<<4) + d; break;
	  case 10: hdr = (hdr<<4) + d; break;
	  case 11: hdr = (hdr<<4) + d;
	    DecodeTbmHeader(hdr, evNr, stkCnt);
	    roc_n = -1;
	    break;

	  case 12: trl = d; break;
	  case 13: trl = (trl<<4) + d; break;
	  case 14: trl = (trl<<4) + d; break;
	  case 15: trl = (trl<<4) + d;
	    DecodeTbmTrailer(trl, dataId, dataNr);
	    break;
	  }
      }
  }
  //Single ROC
  else {
    while (!(pos >= int(data.size()))) {
      // check header
      if ((data[pos] & 0x8ffc) != 0x87f8)
	return -2; // wrong header
      int hdr = data[pos++] & 0xfff;
      // read pixels while not data end or trailer
      while (!(pos >= int(data.size()) || (data[pos] & 0x8000))) {
        // store 24 bits in raw
	raw = (data[pos++] & 0xfff) << 12;
	if (pos >= int(data.size()) || (data[pos] & 0x8000))
	  return -3; // incomplete data
	raw += data[pos++] & 0xfff;
	DecodePixel(raw, n_pix, ph_pix, col, row);
        n.push_back(n_pix);
        ph.push_back(ph_pix);
        address = 0;
        address = (address << 8) ;
        address = (address << 8) + col;
        address = (address << 8) + row;
        adr.push_back(address);
      }
    }
  }
}



// --- event lister ---------------------------------------------------------

class CStore : public CAnalyzer
{
  CRocEvent* Read();
};


CRocEvent* CStore::Read()
{
  CRocEvent *data = Get();
  //  printf("%8u: %03X %4u:\n", (unsigned int)(data->eventNr), (unsigned int)(data->header), (unsigned int)(data->pixel.size()));
  return data;
}


// --- column statistics ----------------------------------------------------

class CColActivity : public CAnalyzer
{
  unsigned long colhits[52];
  CRocEvent* Read();
public:
  CColActivity() { Clear(); }
  void Clear();
};


void CColActivity::Clear()
{
  for (int i=0; i<52; i++) colhits[i] = 0;
}


//CRocEvent* CColActivity::Read()
//{
//  CRocEvent *data = Get();
//  list<CPixel>::iterator i;
//  for (i = data->pixel.begin(); i != data->pixel.end(); i++)
//    if (i->x >= 0 && i->x < 52) colhits[i->x]++;
//  return data;
//}


//void Analyzer(CTestboard &tb)
//{
//  CBinaryDTBSource src(tb);
//  CDataRecordScanner rec;
//  CRocDecoder dec;
//  CStore lister;
//  CSink<CRocEvent*> pump;
//
//  src >> rec >> dec >> lister >> pump;
//
//  pump.GetAll();
//}





/******old version from psi46******/
//void DecodePixel(const vector<uint16_t> &x, int &pos, PixelReadoutData &pix)
//{ //PROFILING
//	pix.Clear();
//	unsigned int raw = 0;
//
//	// check header
//	if (pos >= int(x.size())) throw int(1); // missing data
//	if ((x[pos] & 0x8ffc) != 0x87f8) throw int(2); // wrong header
//	pix.hdr = x[pos++] & 0xfff;
//
//	if (pos >= int(x.size()) || (x[pos] & 0x8000)) return; // empty data readout
//
//	// read first pixel
//	raw = (x[pos++] & 0xfff) << 12;
//	if (pos >= int(x.size()) || (x[pos] & 0x8000)) throw int(3); // incomplete data
//	raw += x[pos++] & 0xfff;
//	pix.n++;
//
//	// read additional noisy pixel
//	int cnt = 0;
//	while (!(pos >= int(x.size()) || (x[pos] & 0x8000))) { pos++; cnt++; }
//	pix.n += cnt / 2;
//
//	pix.p = (raw & 0x0f) + ((raw >> 1) & 0xf0);
//	raw >>= 9;
//	int c =    (raw >> 12) & 7;
//	c = c*6 + ((raw >>  9) & 7);
//	int r =    (raw >>  6) & 7;
//	r = r*6 + ((raw >>  3) & 7);
//	r = r*6 + ( raw        & 7);
//	pix.y = 80 - r/2;
//	pix.x = 2*c + (r&1);
//}


// ==========================================================================

/*
#define ERROR_RO_EMPTY      0
#define ERROR_RO_MISSING    1
#define ERROR_RO_ALIGNMENT  2
#define ERROR_RO_HEADER     3
#define ERROR_RO_DATASIZE   4
*/

// --- event lister ---------------------------------------------------------

CRocEvent* CReadback::Read()
{
	return Get();
}


CRocEvent* CPulseHeight::Read()
{
	return Get();
}


void Analyzer(CTestboard &tb)
{
/*	CDtbSource src(tb, false);
	CDataRecordScanner rec;
	CRocDecoder dec;
	CSink<CRocEvent*> pump;

	src >> rec >> dec >> pump;

	pump.GetAll(); */
}

