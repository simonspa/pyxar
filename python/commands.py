import cmd
import os
import readline

class exit_cmd(cmd.Cmd, object):
    def can_exit(self):
        return True
    def onecmd(self, line):
        r = super (exit_cmd, self).onecmd(line)
        if r and (self.can_exit() or
           raw_input('exit anyway ? (yes/no):')=='yes'):
             return True
        return False
    def do_exit(self, s):
        return True
    def help_exit(self):
        print "Exit the interpreter."
        print "You can also use the Ctrl-D shortcut."
    do_EOF = do_exit
    help_EOF= help_exit

class shell_cmd(exit_cmd, object):
    def do_shell(self, s):
        os.system(s)
    def help_shell(self):
        print "execute shell commands"

class CmdTB(shell_cmd, object):
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
        args = line.split()
        for arg in args[1:]:
            try: 
                arg = int(arg)
            except ValueError:
                pass
        getattr(self.tb, args[0])(*args[1:])


class PyCmd(CmdTB, object):
    """Simple command processor example."""
    def __init__(self):
        super(PyCmd, self).__init__()
        self.prompt = 'pyXar > '
        self.directory = 'data'

    def help_init(self):
        print "Initialize DUT and TB as specified in module and tb config."

    def do_DacDac(self, line):
        #TODO Expose to cui
        self.dut.roc(0).pixel(5,5).active = True
        self.dut.roc(1).pixel(5,5).active = True
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
    
    def do_Pretest(self, line):
        self.run_test('Pretest')
    
    def do_SCurves(self, line):
        self.run_test('SCurves')
    
    def do_PHCalibration(self, line):
        self.run_test('PHCalibration')
    
    def do_FullTest(self, line):
        self.run_test('Calibrate')
        self.run_test('BondMap')
        self.run_test('SCurves')
        self.run_test('PHCalibration')
        self.run_test('Trim')
