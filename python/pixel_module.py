import sys
import copy
import logging 
import numpy
import ROOT

class Pixel(object):

    def __init__(self, col, row, trim = 15, mask = False):
        self._col = col
        self._row = row
        self.mask = mask
        self.trim = trim
        self.active = False
        self._data = None
        self._ph_fit_slope = False
        self._ph_fit_offset = False

    @property
    def col(self):
        return self._col

    @property
    def row(self):
        return self._row

    @property
    def trim(self):
        if self.mask:
            return -1
        else:
            return copy.copy(self._trim)

    @trim.setter
    def trim(self,value):
        if isinstance(value, bool):
            if value == False:
                self._trim = 15
            else:
                raise Exception("Trim Value must be integer in [0,15]")
        else:
            try:
                trim_value = int(value)
            except ValueError:
                raise Exception("Trim Value must be integer in [0,15]")
            # make sure it's not a mask information (-1)
            if not trim_value == -1:
                assert trim_value < 16
                self._trim = trim_value
    
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, set_data):
        self._data = set_data

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        self._mask = bool(value)
        return self._mask

    def __str__(self):
        return "Pixel %s, %s"%(self._col,self._row)

    def __repr__(self):
        return "Pixel %s, %s"%(self._col,self._row)

    #convert PH in ADC to Vcal units
    def ADC_to_Vcal(self, ph):
        if self._ph_fit_slope == False or self._ph_offset == False or self._ph_slope == 0:
            return 0
        else:
            ph_cal = (ph - self._ph_fit_offset)/(self._ph_fit_slope)
            return ph_cal


class DAC(object):
    
    def __init__(self,number, name, bits = 8, value=0):
        self._number = number
        self._name = name
        self._bits = bits
        self.value = value
        self.stored_value = value

    def store(self):
        self.stored_value = self.value

    @property
    def changed(self):
        return self.stored_value != self.value

    @property
    def number(self):
        return self._number

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value
    
    @property
    def range(self):
        return 2**self._bits

    @value.setter
    def value(self,value):
        try:
            set_value = int(value)
        except ValueError:
            raise Exception("DAC Value must be integer in [0,%s]"%2**self._bits)
        assert set_value < 2**self._bits
        self._value = set_value
        return self._value

    def __str__(self):
        return "DAC %s: %s"%(self._name,self._value)

    def __repr__(self):
        return "DAC %s: %s"%(self._number,self._value)
    

class Roc(object):

    def __init__(self, config,number=0,trimVcal=''):
        self.logger = logging.getLogger(self.__class__.__name__)
        """Initialize ROC (readout chip)."""
        self._n_rows = int(config.get('ROC','rows'))
        self._n_cols = int(config.get('ROC','cols'))
        self._n_pixels = self._n_rows*self._n_cols
        self.number = number
        shape = (self._n_cols, self._n_rows)
        self._data = numpy.zeros(shape)
        n_rocs = eval(config.get('Module','rocs'))
        self.flag = 0
        self._ph_array = [0]
        self._ph_cal_array = [0]
        self._ph_slope = numpy.zeros(shape)
        self._ph_offset = numpy.zeros(shape)
        for col in range(51):
            for row in range(79):
                self._ph_slope[col][row] = None
                self._ph_offset[col][row] = None
        self._work_dir = config.get('General','work_dir')

        try:
            self.dacParameterFile = open('%s/dacParameters%s_C%s.dat'%(self._work_dir, trimVcal, self.number))
        except IOError:
            self.dacParameterFile = None
            self.logger.warning('could not open dacParameter file for ROC %i:'%self.number)
            self.logger.warning('%s/dacParameters%s_C%s.dat'%(self._work_dir, trimVcal, self.number) )
            try:
                self.logger.warning('using dacParameters_C0.dat for ROC %s'%self.number)
                self.dacParameterFile = open('%s/dacParameters_C0.dat'%(self._work_dir))
            except IOError:
                self.dacParameterFile = None
                self.logger.error('could not open dacParameter file for ROC 0')
                self.logger.error('%s/dacParameters_C0.dat'%self._work_dir )
                self.logger.error('exiting')
                sys.exit(-1)
        try:
            self.trimParameterFile = open('%s/trimParameters%s_C%s.dat'%(self._work_dir, trimVcal, self.number))
        except IOError:
            self.trimParameterFile = None
            self.logger.warning('could not open trimParameter file for ROC %i'%self.number)

        #define pixel array
        self._pixel_array = []
        # fill pixel array, including trim info
        for col in range(self._n_cols):
            self._pixel_array.append(copy.copy([]))
            for row in range(self._n_rows):
                if self.trimParameterFile:
                    trim, _ , Tcol, Trow = self.trimParameterFile.readline().split()
                    assert int(Tcol) == col and int(Trow) == row
                    self._pixel_array[col].append(Pixel(col, row, trim))
                else:
                    self._pixel_array[col].append(Pixel(col, row))

        #define dac list
        self._dac_dict = {}
        self._dac_number_to_name = {}

        for line in self.dacParameterFile.readlines():
            num, dac_name, val = line.split()
            dac_number = int(num)
            self._dac_number_to_name[dac_number] = dac_name
            #Python 2.2
            self._dac_name_to_number = dict([(v, k) for k, v in self._dac_number_to_name.iteritems()]) 
            #Python 2.7
            #self._dac_name_to_number = {v:k for k, v in self._dac_number_to_name.items()}
            dac_bits = eval(config.get('ROC','dac_bits'))
            self._dac_dict[dac_number] = (DAC(dac_number,dac_name,dac_bits[dac_number],int(val)))

        if self.dacParameterFile:
            self.dacParameterFile.close()
        if self.trimParameterFile:
            self.trimParameterFile.close()

    @property
    def trim_for_tb(self):
        '''Trim bits are just a flat list in interface'''
        #TODO think of a better way in the lower level?
        trim_bits_for_tb = [0] * (self.n_cols*self._n_rows)
        for pix in self.pixels():
            trim_bits_for_tb[pix.col * self.n_rows + pix.row] = pix.trim
        return trim_bits_for_tb
    
    @property
    def trim(self):
        trim_bits = numpy.empty([self.n_cols,self.n_rows],dtype=int)
        trim_bits.fill(15)
        for pix in self.pixels():
            trim_bits[pix.col][pix.row] = copy.copy(pix.trim)
        return trim_bits
        
    @trim.setter
    def trim(self, trim_bits):
        for pix in self.pixels():
            pix.trim = trim_bits[pix.col][pix.row]
            #if (pix.col == 0 and pix.row == 2):
            #    self.logger.debug('%s %s' %(pix, pix.trim))

    def save_trim(self, file_name, directory = None):
        if not directory:
            directory = self._work_dir
        try:
            #TODO think of path
            trimParameterFile = open('%s/trimParameters%s_C%s.dat'%(directory, file_name, self.number),'w')
        except IOError:
            trimParameterFile = None
            self.logger.warning('could not open trimParameter file for ROC %i'%self.number)
        for pixel in self.pixels():
            line = '{0:2d} Pix {1:2d} {2:2d}\n'.format(pixel.trim, pixel.col, pixel.row)
            trimParameterFile.write(line)
        trimParameterFile.close()

    def save_dacs(self, file_name, directory = None):
        if not directory:
            directory = self._work_dir
        try:
            #TODO think of path
            dacParameterFile = open('%s/dacParameters%s_C%s.dat'%(directory, file_name, self.number),'w')
        except IOError:
            dacParameterFile = None
            self.logger.warning('could not open dacParameter file for ROC %i'%self.number)
        for dac in self.dacs():
            line = '{0:3d} {1:15s} {2:3d}\n'.format(dac.number, dac.name, dac.value)
            dacParameterFile.write(line)
        dacParameterFile.close()

    def save(self, file_name, directory = None):
        self.save_trim(file_name, directory)
        self.save_dacs(file_name, directory)
    
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, set_data):
        self._data = set_data
    
    @property
    def ph_array(self):
        return self._ph_array

    @ph_array.setter
    def ph_array(self, set_data):
        self._ph_array = set_data
 
    @property
    def ph_cal_array(self):
        return self._ph_cal_array

    @ph_cal_array.setter
    def ph_cal_array(self, set_data):
        self._ph_cal_array = set_data
    
    @property
    def ph_slope(self):
        return self._ph_slope

    @ph_slope.setter
    def ph_slope(self, set_data):
        self._ph_slope = set_data
 
    @property
    def ph_offset(self):
        return self._ph_offset

    @ph_offset.setter
    def ph_offset(self, set_data):
        self._ph_offset = set_data
 


    @property
    def n_rows(self):
        """Get number of rows."""
        return self._n_rows

    @property
    def n_cols(self):
        """Get number of columns."""
        return self._n_cols
    
    @property
    def n_pixels(self):
        """Get number of pixels."""
        return self._n_pixels

    #get pixel object
    def pixel(self,col,row):
        return self._pixel_array[col][row]

    # get dac object
    def dac(self,dac_id):
        if isinstance(dac_id,str):
            return self._dac_dict[self._dac_name_to_number[dac_id]]
        elif isinstance(dac_id,int):
            return self._dac_dict[dac_id]
    
    #iterator over dacs
    def dacs(self):
        return self._dac_dict.values()

    #iterator over all pixels
    def pixels(self):
        col = 0
        while col < self._n_cols:
            row = 0
            while row < self._n_rows:
                yield self._pixel_array[col][row]
                row += 1
            col += 1
    
    def active_pixels(self):
        col = 0
        while col < self._n_cols:
            row = 0
            while row < self._n_rows:
                if self.pixel(col, row).active: 
                    yield self.pixel(col, row)
                row += 1
            col += 1

    #iterator over column
    def col(self,col):
        row = 0
        while row < self._n_rows:
            yield self._pixel_array[col][row]
            row += 1

    #iterator over row
    def row(self,row):
        col = 0
        while col < self._n_cols:
            yield self._pixel_array[col][row]
            col += 1

    def store_dacs(self):
        for dac in self.dacs():
            dac.store()

    def mask(self,maskbit):
        for pixel in self.pixels():
            pixel.mask = maskbit

    def __repr__(self):
        return "ROC %s"%self.number

    def __str__(self):
        return "ROC %s"%self.number

    #reads in and fits the PhCalibration data and gives back an array of fit parameters for every pixel
    def PHcal_fit(self):
        try:
            self.phCalibrationFile = open('%s/phCalibration_C%s.dat' %(self._work_dir, self.number))
            shape = (self._n_cols, self._n_rows)
            slope_array = numpy.zeros(shape)
            offset_array = numpy.zeros(shape)
            #skip first 4 lines of PhCalibration data file
            header1 = self.phCalibrationFile.readline()
            header2 = self.phCalibrationFile.readline()
            header3 = self.phCalibrationFile.readline()
            header4 = self.phCalibrationFile.readline()

            #loop over lines
            n=5 #keep the first n Vcal points for fitting
            line_number=0
            x=[50.,100.,150.,200.,250.]
            for line in self.phCalibrationFile:
                line = line.strip()
                entries = line.split()
                y = numpy.array(entries[:n])
                y = y.astype(float)
                col = entries[11]
                row = entries[12]
                lf = ROOT.TLinearFitter(1)
                lf.SetFormula("pol1")
                lf.AssignData(n, 1, numpy.array(x), numpy.array(y))
                return_value = lf.Eval()
                if return_value != 0:
                    self.logger.debug('PhCalibration data fit failed in ROC %s pixel (%i,%i)' %self.number,col,row)
                slope = lf.GetParameter(1)
                offset = lf.GetParameter(0)
                #TODO: give warning if chi2 is too large
                slope_array[col,row] = slope
                offset_array[col,row] = offset 
            self.phCalibrationFile.close()
            return slope_array, offset_array

        except IOError:
            self.phCalibrationFile = None
            self.logger.warning('could not open phCalibration file for ROC %i:' %self.number)

    #convert PH in ADC to Vcal units
    def ADC_to_Vcal(self, col, row, ph, slopes, offsets):
        if self.flag == 0:
            return 0
        else:
            self.pixel(col,row)._ph_fit_slope = slopes[col][row]
            self.pixel(col,row)._ph_fit_offset = offsets[col][row]
            if self.pixel(col,row)._ph_fit_slope == None or self.pixel(col,row)._ph_fit_offset == None or self.pixel(col,row)._ph_fit_slope == 0:
                return 0
            else:
                ph_cal = (ph - self.pixel(col,row)._ph_fit_offset)/(self.pixel(col,row)._ph_fit_slope)
                return ph_cal

class TBM(object):
    def __init__(self,config,number=0):
        self._n_channels = int(config.get('TBM','channels'))
        self.number = number

    def __repr__(self):
        return "TBM %s"%self.number

    def __str__(self):
        return "TBM %s"%self.number

class DUT(object):
    def __init__(self, config, trimVcal = ''):
        self.logger = logging.getLogger(self.__class__.__name__)
        """Initialize Module"""
        self._work_dir = config.get('General','work_dir')

        #define collections
        self._roc_list = []
        self._tbm_list = []

        # fill collections
        n_rocs = eval(config.get('Module','rocs'))
        if type(n_rocs) == int:
            self._n_rocs = n_rocs
            for roc in range(self._n_rocs):
                self._roc_list.append(Roc(config,roc,trimVcal))
        elif type(n_rocs) == list:
            self._n_rocs = len(n_rocs)
            for roc in n_rocs:
                self._roc_list.append(Roc(config,roc,trimVcal))

        self._n_tbms = int(config.get('Module','tbms'))
        for tbm in range(self._n_tbms):
            self._tbm_list.append(TBM(config,tbm))

        try:
            self.MaskFile = open('%s/MaskFile.dat'%(self._work_dir))
            self.logger.info('using pixel Mask File')
        except IOError:
            self.MaskFile = None

        if self.MaskFile:
            for line in self.MaskFile.readlines():
                if not line.startswith('#'):
                    line = line.split()
                    if line[0] == 'pix':
                        self.pixel(int(line[1]),int(line[2]),int(line[3])).mask = True
                    if line[0] == 'col':
                        for pix in self.roc(int(line[1])).col(int(line[2])):
                            pix.mask = True
                    if line[0] == 'row':
                        for pix in self.roc(int(line[1])).row(int(line[2])):
                            pix.mask = True
                    if line[0] == 'roc':
                        for pix in self.roc(int(line[1])).pixels():
                            pix.mask = True

            self.MaskFile.close()

    def _activate_pixel(self, val, *args):
        if len(args) == 3:
            roc,col,row = args
            self.pixel(roc,col,row).active = bool(val)

    def activate_pixel(self, *args):
        self._activate_pixel(True, *args)

    def deactivate_pixel(self, *args):
        self._activate_pixel(False, *args)

    @property
    def data(self):
        return numpy.array([roc.data for roc in self.rocs()])
 
    @data.setter
    def data(self, set_data):
        for roc in self.rocs():
            roc.data = set_data[roc.number]

    @property
    def ph_array(self):
        ph_array = [roc.ph_array for roc in self.rocs()]
        return ph_array


    @ph_array.setter
    def ph_array(self, set_data):
        for roc in self.rocs():
            roc.ph_array = set_data[roc.number]

    @property
    def ph_cal_array(self):
        ph_cal_array = [roc.ph_cal_array for roc in self.rocs()]
        return ph_cal_array


    @ph_cal_array.setter
    def ph_cal_array(self, set_data):
        for roc in self.rocs():
            roc.ph_cal_array = set_data[roc.number]



    @property
    def pixel_data(self):
        pixel_data = numpy.array([])
        for roc in self.rocs():
            pixel_data.extend([pixel.data for pixel in roc.pixels()])
        return pixel_data

    @property
    def trim(self):
        return numpy.copy(numpy.array([roc.trim for roc in self.rocs()]))

    @trim.setter
    def trim(self, trim_bits):
        for roc in self.rocs():
            roc.trim = trim_bits[roc.number]

    @property
    def n_rocs(self):
        return self._n_rocs

    @property
    def n_tbms(self):
        return self._n_tbms
    
    #get tbm object
    def tbm(self,roc):
        return self._tbm_list[roc]
    

    #iterator over tbms
    def tbms(self):
        tbm = 0
        while tbm < self._n_tbms:
            yield self.tbm(tbm)
            tbm += 1

    #get roc object
    def roc(self,roc):
        return self._roc_list[roc]
    
    #iterator over rocs
    def rocs(self):
        roc = 0
        while roc < self._n_rocs:
            yield self.roc(roc)
            roc += 1

    #get pixel object
    def pixel(self,roc,col,row):
        return self.roc(roc).pixel(col,row)

    #get dac object
    def dac(self,roc,dac_id):
        return self.roc(roc).dac(dac_id)

    def store_dacs(self):
        for roc in self.rocs():
            roc.store_dacs()

    def get_roc_shape(self):
        roc = self._roc_list[0]
        return (roc.n_cols,roc.n_rows)

    @property
    def n_cols(self):
        return self._roc_list[0].n_cols

    @property
    def n_rows(self):
        return self._roc_list[0].n_rows

    def dacs(self):
        return self._roc_list[0].dacs()

if __name__=='__main__':
    from BetterConfigParser import BetterConfigParser
    config = BetterConfigParser()
    config.read('../data/module')
    logging.basicConfig(level=logging.INFO) 
    #make a module from config
    m = DUT(config)

    #access a single pixel
    print m.roc(0).pixel(12,13)
    #or
    print m.pixel(0,12,13)
    print m.pixel(0,12,13).trim

    print m.roc(0).dac('Vana')
    #iterate
    for roc in m.rocs():
        roc.dac('Vana').value = 155
        print roc, roc.dac('Vana')

    #set individual DAC, by name or number
    m.roc(0).dac('Vana').value = 0
    print m.roc(0).dac('Vana')
    m.roc(0).dac(2).value = 0
    print m.roc(0).dac('Vana')

    print m.pixel(0,2,1).mask

    #mask a single pixel
    #m.pixel(0,45,6).mask = True
    #print m.roc(0).mask
    #unmask all pixels of roc 2
    #m.roc(0).mask = False
    #print m.roc(0).mask
