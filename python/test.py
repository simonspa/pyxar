
class Test(object):

    def __init__(self, tb, config, a_test):
        self.tb = tb
        self.config = config
        self.name = a_test
        self._results = None

    def run_roc(self, roc):
        print 'Running %s ' %(self.name)
        self._results = getattr(self.tb, self.name)(roc)
    
    def run_tbm(self, tbm):
        pass

    def run_module(self, module):
        for roc in module.rocs:
            run_roc(roc)
        run_tbm(module.tbm)
    
    @property
    def results(self):
        return self._results
