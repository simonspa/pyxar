# pyXar

Python wrapper to run single ROC and module tests using a DTB.

### dependencies:
- python2.7
- cython (http://cython.org/)
- numpy (http://www.numpy.org)
- pyROOT (http://root.cern.ch/drupal/content/pyroot)
- pxarCore (compile pxar using `cmake -DBUILD_python=ON .. && make install`)

### usage:

To start pyxar, make sure to set the library paths, and run:

    ./pyXar
    
Specify the input directory with:

    ./pyXar --dir PATH

### implementing a test:

All tests inherit from the base class Test in test.py
For a test to be included in the fraework the new class must be importet in the 

    python/__init__.py
file under pyhton

tests usually contains at least the method run()

Two additional methods prepare() and cleanup() give the usual structure of a test.

- The base class provides all necessary obejcts like tb and dut.
- DAC parameters changed during the test will be automatically reset.
- The docstring of the class is displayed as help message in the command line interface.


### Prepare the pxarCore library:
Get pxar from its github repositoryand build it

```
mkdir build
cmake -DBUILD_python=ON ..
make install
```

Export the path to the library:

```
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:PATH/TO/API/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:PATH/TO/API/lib
export PYTHONPATH=$PYTHONPATH:PATH/TO/API/lib
```
or use the `pyXar.sh` script which assumes pxar is installed along the pyxar directory.
    
To start pyxar using the API, run:

```
./pyXar --api
```
