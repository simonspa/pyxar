import test

class Threshold(test.Test):
    
    def prepare(self, config): 
        self.cals = int(eval(config.get('Threshold','cals')))
        self.xtalk = int(eval(config.get('Threshold','xtalk')))
        self.dac = config.get('Threshold','dac')
        self.n_triggers = int(config.get('Threshold','n_triggers'))
        self.reverse = eval(config.get('Threshold','reverse'))

    def run(self, config): 
        self.logger.info('Running threshold test')
        self.tb.SignalProbe("a1","ctr")
        self.tb.SignalProbe("a2","clk")
        dut_thr_map = self.tb.get_threshold(self.n_triggers, self.dac, self.xtalk, self.cals, self.reverse) 
