import test

class BondMap(test.Test):
    
    def prepare(self, config): 
        self.cals = int(True)
        self.xtalk = int(False)
        self.dac = 'VthrComp'
        self.n_triggers = int(config.get('BondMap','n_triggers'))
        self.reverse = False

    def run(self, config): 
        self.logger.info('Running BondMap')
        self.tb.set_dac('CtrlReg', 4)
        dut_thr_map = self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse) 
