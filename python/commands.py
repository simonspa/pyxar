import cmd
import readline

class CmdTB(cmd.Cmd,object):
    def __init__(self):
        super(CmdTB, self).__init__()
        self.TB = ['ia','id','init_dut','set_dac']
        #TODO, get rid of this, needed on OSX109
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
    
    def complete_tb(self, f, text, line, begidx, endidx):
        if not text:
            completions = self.TB[:]
        else:
            completions = [ f
                            for f in self.TB
                            if f.startswith(text)
                            ]
        return completions
    
    def do_tb(self, line):
        print 'Running tb %s' %line
        #TODO Think of better way of parsing
        getattr(self.tb, line)


class PyCmd(CmdTB, object):
    """Simple command processor example."""
    def __init__(self):
        super(PyCmd, self).__init__()

    def help_init(self):
        print "Initialize DUT and TB as specified in module and tb config."

    def do_DacDac(self, line):
        #TODO Expose to cui
        self.dut.roc(0).pixel(5,5).active = True
        self.run_test('DacDac')
    
    def help_DacDac(self):
        print "Run a DacDac scan using the DACs from test.cfg"
    
    def do_Threshold(self, line):
        self.run_test('Threshold')
    
    def help_Threshold(self):
        print "Run a Threshold scan using the DACs from test.cfg"
        
    def do_Calibrate(self, line):
        self.run_test('Calibrate')
    
    def help_Calibrate(self):
        print "Send calibrates to the DUT, n_triggers specified test.cfg"
    
    def do_BondMap(self, line):
        self.run_test('BondMap')
    
    def help_BondMap(self):
        print "Run a bond map"
    
    def do_Trim(self, line):
        self.run_test('Trim')
    
    def help_Trim(self):
        print "Trim the DUT to values specified in test.cfg"
    
    def do_SCurves(self, line):
        self.run_test('SCurves')
    
    def do_EOF(self, line):
        return True
    
    def help_EOF(self):
        print "Exit"
    
    def do_exit(self, line):
        return True
    
    def help_exit(self):
        print "Exit"

    def do_shell(self, s):
        os.system(s)
    
    def help_shell(self):
        print "execute shell commands"
