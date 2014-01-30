import hrtest

class HRMap(hrtest.HRTest):

    def prepare(self, config):
        self.data_taking_time = int(config.get('HR','data_taking_time'))
        ttk = int(config.get('HR','ttk'))
        period = int(config.get('HR','period'))
        for roc in self.dut.rocs():
            for col in range(roc.n_cols):
                self.tb.enable_column(col)
        self.tb.pg_stop()
        self.tb.init_deser()
        self.tb.daq_enable() 
        self.tb.pg_setcmd(0, self.tb.PG_RESR)
        self.tb.pg_single()
        self.tb.pg_setcmd(0, self.tb.PG_TRG  + ttk)
        self.tb.pg_setcmd(1, self.tb.PG_TOK)
        self.tb.pg_loop(1288)
