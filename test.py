import sys
import cmd
import subprocess
import logging
from optparse import OptionParser
from python import Testboard
from python import Roc
from python import DacDac, Calibrate
from python import Plotter
from python import BetterConfigParser
logging.basicConfig(level=logging.INFO)

class Pxar(cmd.Cmd):
    """Simple command processor example."""
    
    def do_init(self, line):
        configs = ['data/general','data/roc','data/tb']
        self.config = BetterConfigParser()
        self.config.read(configs)
        self.tb = Testboard(self.config)
        self.obj = Roc(self.config)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initialzed testboard')

        self.TESTS = ['mask_test','chip_efficiency','DacDac']
    
    def str_to_class(str):
        return reduce(getattr, str.split("."), sys.modules[__name__])

    def do_test(self, line):
        a_test = globals()[line](self.tb, self.obj, self.config)
        a_test.run(self.config)
        plot = Plotter(self.config, a_test)
        plot.do_plot()
    
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
        self.do_test('DacDac')
        
    def do_Calibrate(self, line):
        self.do_test('Calibrate')
    
    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    pxar = Pxar()
    pxar.cmdloop()
