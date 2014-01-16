rm dtb.so
rm python/dtb.so
rm python/dtb.cpp
CXXFLAGS="-g -Os -Wall" \
LDFLAGS=" -lftd2xx" \
python setup.py build_ext -i
cp dtb.so python/
