import sys
import cmd
import subprocess
import logging
import ROOT
from optparse import OptionParser
from python import Testboard
from python import DUT
from python import DacDac, Calibrate, Threshold
from python import Plotter
from python import BetterConfigParser
from gui import PxarGui
logging.basicConfig(level=logging.INFO)

class Pxar(cmd.Cmd):
    """Simple command processor example."""
    
    def do_init(self, line):
        configs = ['data/general','data/module','data/tb','data/test.cfg']
        self.config = BetterConfigParser()
        self.config.read(configs)
        self.dut = DUT(self.config)
        self.tb = Testboard(self.config, self.dut)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initialzed testboard')

        self.TESTS = ['Calibrate','DacDac']
        self.TB = ['getia','getid']
    
    def str_to_class(str):
        return reduce(getattr, str.split("."), sys.modules[__name__])

    def do_test(self, line):
        a_test = globals()[line](self.tb, self.config)
        a_test.run(self.config)
        plot = Plotter(self.config, a_test)
        hist = plot.do_plot()
        window.histos.append(plot.data)
        window.update()
    
    def complete_test(f, text, line, begidx, endidx):
        if not text:
            completions = self.TESTS[:]
        else:
            completions = [ f
                            for f in self.TESTS
                            if f.startswith(text)
                            ]
        return completions

    def do_DacDac(self, line):
        #TODO Expose to gui/cui
        self.dut.roc(0).pixel(5,5).active = True
        self.do_test('DacDac')
    
    def do_Threshold(self, line):
        self.do_test('Threshold')
        
    def do_Calibrate(self, line):
        self.do_test('Calibrate')
    
    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    window = PxarGui( ROOT.gClient.GetRoot(), 800, 800 )
    pxar = Pxar()
    pxar.cmdloop()
