pyxar
=======

Python wrapper to run single ROC and module tests using a DTB.

### dependencies:
- python2.7
- cython
- numpy
- pyROOT
- usb ftdi driver


### usage
For compilation and running cython, numpy and libftdi2xx

CYTHON
    easy_install cython

NUMPY
http://www.numpy.org/

LIBFTDI2XX
http://www.ftdichip.com/Drivers/D2XX.htm

To compile the library run:
    python setup.py build_ext

To start pyxar, run:
    ./pyXar
