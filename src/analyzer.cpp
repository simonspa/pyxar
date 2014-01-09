// analyzer.cpp

#include "analyzer.h"
#include <stdio.h>

using namespace std;


void DumpData(const vector<uint16_t> &x, unsigned int n)
{
	printf("\n");
	unsigned int i;
	printf("\n%i samples\n", int(x.size()));
	for (i=0; i<n && i<x.size(); i++)
	{
		if (x[i] & 0x8000) printf(">"); else printf(" ");
		//printf("%03X", (unsigned int)(x[i] & 0xfff));
		printf("%04X", (unsigned int)(x[i] & 0xfff));
		if (i%16 == 15) printf("\n");
	}
	printf("\n");
}

void DecodeTbmHeader(unsigned int raw)
{
	int evNr = raw >> 8;
	int stkCnt = raw & 6;
	printf("  EV(%3i) STF(%c) PKR(%c) STKCNT(%2i)",
		evNr,
		(raw&0x0080)?'1':'0',
		(raw&0x0040)?'1':'0',
		stkCnt
		); 
}

void DecodeTbmTrailer(unsigned int raw)
{
	int dataId = (raw >> 6) & 0x3;
	int data   = raw & 0x3f;
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

void DecodePixelRaw(unsigned int raw)
{
	unsigned int ph = (raw & 0x0f) + ((raw >> 1) & 0xf0);
	raw >>= 9;
	int c =    (raw >> 12) & 7;
	c = c*6 + ((raw >>  9) & 7);
	int r =    (raw >>  6) & 7;
	r = r*6 + ((raw >>  3) & 7);
	r = r*6 + ( raw        & 7);
	int y = 80 - r/2;
	int x = 2*c + (r&1);
	printf("   Pixel [%05o] %2i/%2i: %3u", raw, x, y, ph);
}

void DecodePixelW(const vector<uint16_t> &data, int &pos, PixelReadoutData &pix)
{ 

    uint32_t words_remaining = 0;
    int TBM_eventnr,TBM_stackinfo,ColAddr,RowAddr,PulseHeight,TBM_trailerBits,TBM_readbackData;
    int size = data.size();
	printf("#samples: %i  remaining: %i\n", size, int(words_remaining));
    unsigned int hdr, trl;
	unsigned int raw;
	for (int i=0; i<size; i++)
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
			     DecodePixelRaw(raw);
				 break;

		case  7: printf("\nROC-HEADER(%1X): ", d); break;

		case  8: printf("\n\nTBM H1(%1X) ", d); hdr = d; break;
		case  9: printf("H2(%1X) ", d);       hdr = (hdr<<4) + d; break;
		case 10: printf("H3(%1X) ", d);       hdr = (hdr<<4) + d; break;
		case 11: printf("H4(%1X) ", d);       hdr = (hdr<<4) + d; 
			     DecodeTbmHeader(hdr);
			     break;

		case 12: printf("\nTBM T1(%1X) ", d); trl = d; break;
		case 13: printf("T2(%1X) ", d);       trl = (trl<<4) + d; break;
		case 14: printf("T3(%1X) ", d);       trl = (trl<<4) + d; break;
		case 15: printf("T4(%1X) ", d);       trl = (trl<<4) + d;
			     DecodeTbmTrailer(trl);
			     break;
		}
	}

	printf("\n");
/*
	pix.Clear();

	// check header
	if (pos >= int(data.size())) {
        //printf("Missing data");
        throw int(1); // missing data
    }
	if ((data[pos] & 0x8ffc) != 0x87f8){
        //printf("Wrong header");
         throw int(2); // wrong header
    }
	pix.hdr = data[pos++] & 0xfff;

	if (pos >= int(data.size()) || (data[pos] & 0x8000)){
        //printf("Empty readout");
         return; // empty data readout
    }

	// read first pixel
	raw = (data[pos++] & 0xfff) << 12;
	if (pos >= int(data.size()) || (data[pos] & 0x8000)){
        //printf("Incomplete");
         throw int(3); // incomplete data
    }
	raw += data[pos++] & 0xfff;
	pix.n++;

	// read additional noisy pixel
	int cnt = 0;
	while (!(pos >= int(data.size()) || (data[pos] & 0x8000))) { pos++; cnt++; }
	pix.n += cnt / 2;

	pix.p = (raw & 0x0f) + ((raw >> 1) & 0xf0);
	raw >>= 9;
	int c =    (raw >> 12) & 7;
	c = c*6 + ((raw >>  9) & 7);
	int r =    (raw >>  6) & 7;
	r = r*6 + ((raw >>  3) & 7);
	r = r*6 + ( raw        & 7);
	pix.y = 80 - r/2;
	pix.x = 2*c + (r&1);*/
}




// --- event lister ---------------------------------------------------------

class CStore : public CAnalyzer
{
	CRocEvent* Read();
};


CRocEvent* CStore::Read()
{
	CRocEvent *data = Get();
	printf("%8u: %03X %4u:\n", (unsigned int)(data->eventNr), (unsigned int)(data->header), (unsigned int)(data->pixel.size()));
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


CRocEvent* CColActivity::Read()
{
	CRocEvent *data = Get();
	list<CPixel>::iterator i;
	for (i = data->pixel.begin(); i != data->pixel.end(); i++)
		if (i->x >= 0 && i->x < 52) colhits[i->x]++;
	return data;
}


void Analyzer(CTestboard &tb)
{
	CBinaryDTBSource src(tb);
	CDataRecordScanner rec;
	CRocDecoder dec;
	CStore lister;
	CSink<CRocEvent*> pump;

	src >> rec >> dec >> lister >> pump;

	pump.GetAll();
}
