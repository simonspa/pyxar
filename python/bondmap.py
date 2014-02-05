import test

class BondMap(test.Test):
    ''' inject Vcal in high range through the Sensor and determin Threshold. Lower Thresholds (i.e. higher VcThr DAC value) indicate a worse connection of the Sensor Pixel to the ROC PUC '''


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
