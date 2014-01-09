// analyzer.h

#pragma once

#include "pixel_dtb.h"
#include "datastream.h"
#include <vector>
// #include <stdint.h>


struct PixelReadoutData
{
	unsigned int hdr;
	int n;  // # pixel
	int x;  // x of first pixel
	int y;  // y of first pixel
	int p;  // pulse heigth
	void Clear() { hdr = 0; n = x = y = p = 0; }
};


void DumpData(const vector<uint16_t> &x, unsigned int n);

void DecodeTbmTrailer(unsigned int raw);

void DecodeTbmHeader(unsigned int raw);

void DecodePixelRaw(unsigned int raw);

void DecodePixelW(const std::vector<uint16_t> &x, int &pos, PixelReadoutData &pix);
