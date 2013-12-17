import Test

class Calibrate(Test.Test):

    def run(self, config):
        n_triggers = 10
        self._results = self.tb.get_calibrate(n_triggers)
        return
    
