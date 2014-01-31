import hrtest

class HRMap(hrtest.HRTest):

    def prepare(self, config):
        self.data_taking_time = int(config.get('HR','data_taking_time'))
        ttk = int(config.get('HR','ttk'))
        period = int(config.get('HR','period'))
        for roc in self.dut.rocs():
            self.tb.select_roc(roc)
            for col in range(roc.n_cols):
                self.tb.enable_column(col)
        self.tb.pg_stop()
        self.tb.init_deser()
        self.tb.daq_enable() 
        self.tb.pg_setcmd(0, self.tb.PG_RESR)
        self.tb.pg_single()
        if self.dut.n_tbms > 0:
            self.tb.init_pg(self.config)
            #self.tb.pg_setcmd(0, self.tb.PG_RESR + 15)
            #self.tb.pg_setcmd(1, self.tb.PG_CAL + 56)
            #self.tb.pg_setcmd(0, self.tb.PG_SYNC + self.tb.PG_TRG)
            #self.tb.pg_setcmd(1, self.tb.PG_TRG  + ttk)
        else:
            self.tb.pg_setcmd(0, self.tb.PG_TRG  + ttk)
            self.tb.pg_setcmd(1, self.tb.PG_TOK)
        self.tb.pg_loop(period)
