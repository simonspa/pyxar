#!/bin/bash
rm -v dtb.so
rm -v python/dtb.so
rm -v python/dtb.cpp
CXXFLAGS="-g -Os -Wall" \
LDFLAGS=" -lftd2xx" \
python setup.py build_ext -i
cp dtb.so python/
