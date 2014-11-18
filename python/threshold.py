import test

class Threshold(test.Test):
    
    def prepare(self, config): 
        self.cals = int(eval(config.get('Threshold','cals')))
        self.xtalk = int(eval(config.get('Threshold','xtalk')))
        self.dac = config.get('Threshold','dac')
        self.n_triggers = int(config.get('Threshold','n_triggers'))
        self.reverse = int(eval(config.get('Threshold','reverse')))
        self.threshold = 50

    def run(self, config): 
        self.tb.m_delay(7000)
        self.logger.info('Running threshold test')
        dut_thr_map = self.tb.get_threshold(self.n_triggers, self.dac, self.threshold, self.xtalk, self.cals, self.reverse) 
