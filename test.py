import sys
import cmd
import subprocess
from optparse import OptionParser
from python import Testboard
from python import Roc
from python import Test
from python import Plotter
from python import BetterConfigParser

class Pxar(cmd.Cmd):
    """Simple command processor example."""
    #def __init__(self):
    #    super(Pxar, self).__init__()
    
    def do_init(self, line):
        configs = ['data/general','data/roc']
        self.config = BetterConfigParser()
        self.config.read(configs)
        self.tb = Testboard(self.config)
        self.obj = Roc(self.config)
        print "Initialzed TB and ROC"

        self.TESTS = ['mask_test','chip_efficiency','dac_dac']
    
    def do_test(self, line):
        a_test = Test(self.tb, self.config, line)
        a_test.run_roc(self.obj)
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

    def do_dac_dac(self, line):
        self.do_test('dac_dac')
        
    def do_chip_efficiency(self, line):
        self.do_test('chip_efficiency')
    
    def do_mask_test(self, line):
        self.do_test('mask_test')

    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    pxar = Pxar()
    pxar.cmdloop()
