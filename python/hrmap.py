import hrtest

class HRMap(hrtest.HRTest):
    '''Take a high rate pixel map for data_taking_time in seconds, 
period is the trigger frequency, trigger-token-delay (ttc) 
and clock stretch factor (ssc) are additional parameters.'''


    def prepare(self, config):
        self.data_taking_time = int(config.get('HRMap','data_taking_time'))
        ttk = int(config.get('HRMap','ttk'))
        self.period = int(config.get('HRMap','period'))
        self.scc = int(config.get('HRMap','scc'))
        for roc in self.dut.rocs():
            self.tb.select_roc(roc)
            for col in range(roc.n_cols):
                self.tb.enable_column(col)
        self.tb.pg_stop()
        self.tb.init_deser()
        self.tb.daq_enable() 
        self.tb.set_pg([("resetroc",0)])
        self.tb.pg_single(1,2)
        
        #fit PhCalibration data
        self.logger.info('Fitting PHCalibration data...')
        for roc in range(int(config.get('Module','rocs'))):
            self.dut.roc(roc).ph_slope, self.dut.roc(roc).ph_offset, self.dut.roc(roc).ph_par2 = self.dut.roc(roc).PHcal_fit()
        if self.dut.n_tbms > 0:
            self.tb.init_pg(self.config)
            #self.tb.pg_setcmd(0, self.tb.PG_RESR + 15)
            #self.tb.pg_setcmd(1, self.tb.PG_CAL + 56)
            #self.tb.pg_setcmd(0, self.tb.PG_SYNC + self.tb.PG_TRG)
            #self.tb.pg_setcmd(1, self.tb.PG_TRG  + ttk)
        else:
            self.tb.set_pg([("trigger",ttk),
                            ("token",0)])

