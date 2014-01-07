import sys
import os
import logging
import ROOT
from optparse import OptionParser
from python import Testboard
from python import DUT
from python import DacDac, Calibrate, Threshold, Trim, BondMap, SCurves
from python import BetterConfigParser
from gui import PxarGui
from python import PyCmd
from python import colorer
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
__version__ = "PyXar: 0.1"

class Pxar(PyCmd):
    
    def do_init(self, line):
        configs = ['data/general','data/module','data/tb','data/test.cfg']
        self.config = BetterConfigParser()
        self.config.read(configs)
        self.dut = DUT(self.config)
        self.tb = Testboard(self.config, self.dut)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initialzed testboard')
        self.tb.ia()
        self.tb.id()

    @staticmethod
    def str_to_class(str):
        return reduce(getattr, str.split("."), sys.modules[__name__])
    
    def run_test(self, line):
        a_test = globals()[line](self.tb, self.config)
        a_test.go(self.config)
        window.histos.extend(a_test.histos)
        window.update()
 
if __name__ == '__main__':
    window = PxarGui( ROOT.gClient.GetRoot(), 800, 800 )
    pxar = Pxar()
    #TODO remove
    pxar.do_init('')
    pxar.cmdloop(__version__)
