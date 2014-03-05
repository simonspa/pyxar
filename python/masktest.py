import test
import ROOT
import numpy

class MaskTest(test.Test):
    ''' mask all pixels and send n calibrates to each pixels and get readout with address '''

    def prepare(self, config):
        self.n_triggers = int(config.get('MaskTest','n_triggers'))

    def run(self, config):
        mask_list = [-1]*(self.dut.n_cols * self.dut.n_rows)
        for roc in self.dut.rocs():
            self.tb.select_roc(roc)
            self.tb.trim_chip(mask_list)
            self.tb.m_delay(100)
        self.tb.get_calibrate(self.n_triggers)
        # restore
        self.tb.trim(self.dut.trim)

    def cleanup(self, config):
        super(MaskTest, self).cleanup(config)
        for histo in self._histos:
            if type(histo)==ROOT.TH2F:
                histo.SetMinimum(0)
                histo.SetMaximum(self.n_triggers)
