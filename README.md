# pyXar

Python wrapper to run single ROC and module tests using a DTB.

### dependencies:
- python2.7
- cython (http://cython.org/)
- numpy (http://www.numpy.org)
- pyROOT (http://root.cern.ch/drupal/content/pyroot)
- usb driver libftdi2xx (http://www.ftdichip.com/Drivers/D2XX.htm)
- libusb (http://www.libusb.org/)

### usage:

To compile the library run:

    python setup.py build_ext

To start pyxar, run:

    ./pyXar
    
Specify the input directory with:

    ./pyXar --dir PATH

### implementing a test:

All tests inherit from the base class Test in test.py
For a test to be included in the fraework the new class must be importet in the __init__.py file under pyhton

tests usually contains at least the method run()

Two additional methods prepare() and cleanup() give the usual structure of a test.

The base class provdes all necessary obejcts like tb and dut. DAC parameters changed during the test will be automatically reset.
The docstring of the class is displayed as help message in the command line interface


### pyXar also provides a way to run with the API (currently as beta version)
Get the python version of the API and build it

    mkdir build
    cmake -DBUILD_python=ON ..
    make install

Export the path to the library:

    export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:PATH/TO/API/lib
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:PATH/TO/API/lib
    export PYTHONPATH=$PYTHONPATH:PATH/TO/API/lib
    
To start pyxar using the API, run:

    ./pyXar --api
