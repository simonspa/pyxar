import test
import ROOT

class HREfficiency(test.Test):
    ''' send n calibrates to each pixels and get readout with address while DUT is exposed to high x-radiation rate'''

    def prepare(self, config):
        self.n_triggers = int(config.get('HREfficiency','n_triggers'))

    def run(self, config):
        self.tb.get_calibrate(self.n_triggers)

    def cleanup(self, config):
        super(HREfficiency, self).cleanup(config)
        for histo in self._histos:
            if type(histo)==ROOT.TH2F:
                histo.SetMinimum(0)
                histo.SetMaximum(self.n_triggers)
