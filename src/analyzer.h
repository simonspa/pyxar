// analyzer.h

#pragma once

#include "pixel_dtb.h"
#include "datastream.h"
#include <vector>
#include <stdint.h>


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

void DecodePixel(unsigned int raw);

int8_t Decode(const std::vector<uint16_t> &data, std::vector<uint16_t> &n, std::vector<uint16_t> &ph, std::vector<uint32_t> &adr);
