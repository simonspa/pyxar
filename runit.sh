CXXFLAGS="-g -Os -Wall" \
LDFLAGS=" -lftd2xx" \
python setup.py build_ext -i
cp dtb.so python/

