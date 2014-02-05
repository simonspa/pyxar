import test
import ROOT

class Calibrate(test.Test):
    ''' send n calibrates to each pixels and get readout with address '''

    def prepare(self, config):
        self.n_triggers = int(config.get('Calibrate','n_triggers'))

    def run(self, config):
        self.tb.get_calibrate(self.n_triggers)

    def cleanup(self, config):
        super(Calibrate, self).cleanup(config)
        for histo in self._histos:
            if type(histo)==ROOT.TH2F:
                histo.SetMinimum(0)
                histo.SetMaximum(self.n_triggers)
