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
        self.TB = ['ia','id','reset_dut','mask','unmask','set_dac','set_dac_roc','pon','poff','hv_on','hv_off']
        self.DUT = ['activate_pixel', 'deactivate_pixel']
        #TODO, get rid of this, needed on OSX109
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
    
    def complete_tb(self, text, line, begidx, endidx):
        if not text:
            completions = self.TB[:]
        else:
            completions = [ f
                        for f in self.TB
                        if f.startswith(text)
                        ]
        return completions
    
    def do_tb(self, line):
        args = self.get_list(line)
        try:
            getattr(self.tb, args[0])(*args[1:])
        except Exception, e:
            print 'wrong command'
            print e

    def help_tb(self):
        print '''call testboards methods with arguments:
    -tb set_dac DAC VALUE
    -tb set_dac_roc ROC DAC VALUE
    -tb ia (read analog current)
    -tb id (read digital current)
    -tb pon (turn on power to DUT)
    -tb poff (turn off power to DUT)
    -tb hv_on (turn on HV)
    -tb hv_off (turn off HV)
    -tb reset_dut (reload and program TBM and ROC DAC parameters)
    -tb un/mask ROC COL ROW (un/mask single pixel)
    -tb un/mask ROC (un/mask entire ROC)
    -tb un/mask (un/mask entire DUT)'''

    def complete_set_dac(self, text, line, begidx, endidx):
        DACS = [dac.name for dac in list(self.tb.dut.dacs())]
        if not text:
            completions = DACS[:]
        else:
            completions = [ f
                        for f in DACS
                        if f.startswith(text)
                        ]
        return completions

    def do_set_dac(self,line):
        args = self.get_list(line)
        try:
            self.tb.set_dac(*args)
        except Exception, e:
            print 'wrong command'
            print e

    def help_set_dac(self):
        print 'set dac register'


    def complete_dut(self, text, line, begidx, endidx):
        if not text:
            completions = self.DUT[:]
        else:
            completions = [ f
                            for f in self.DUT
                            if f.startswith(text)
                            ]
        return completions
    
    def do_dut(self, line):
        args = self.get_list(line)
        try:
            getattr(self.tb.dut, args[0])(*args[1:])
        except Exception, e:
            print 'wrong command'
            print e

    def help_dut(self):
        print 'call DUT methods with arguments'
        print '\tdut activate_pixel ROC COL ROW\n\tdut deactivate_pixel ROC COL ROW'

    def help_help(self):
        print 'display the help message'

    @staticmethod
    def get_list(line):
        args = line.split()
        for i,arg in enumerate(args):
            try: 
                args[i] = int(arg)
            except ValueError:
                pass
        return args
            
class PyCmd(CmdTB, object):
    """Simple command processor example."""
    def __init__(self):
        super(PyCmd, self).__init__()
        self.prompt = 'pyXar > '
        self.directory = 'data'

        self.fulltest = ['Pretest', 'Calibrate', 'MaskTest', 'SCurves', 'TrimBits', 'BondMap', 'Trim', 'PHCalibration']

        # dinamicaly generate the help and do class methods for the tests
        for test in self.tests:
            self._do_factory(test)
            self._help_factory(test)

    def _do_factory(self, test):
        def _do_test(self, line):
            self.run_test(test)
        _do_test.__name__ = 'do_%s'%test
        setattr(self.__class__,_do_test.__name__,_do_test)

    def _help_factory(self, test):
        def _help_test(self):
            print self.get_help(test)
        _help_test.__name__ = 'help_%s'%test
        setattr(self.__class__,_help_test.__name__,_help_test)

    def help_init(self):
        print "Initialize DUT and TB as specified in module and tb config."

    def do_FullTest(self, line):
        for test in self.fulltest:
            self.run_test(test)

    def help_FullTest(self):
        print 'execute the following list of tests:'
        print ', '.join(self.fulltest)
