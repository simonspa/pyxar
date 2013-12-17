import ROOT

class Plotter(object):

    def __init__(self, config, test):
        self.config = config
        self.name = type(test).__name__
        self.data = self.grid_to_th2(test.results,self.name)

    @staticmethod
    def grid_to_th2(grid,name):
        n_rows = len(grid)
        n_cols = len(grid[0])
        th2 = ROOT.TH2F(name, name, n_cols, 0, n_cols , n_rows, 0, n_rows);
        th2.SetDirectory(0)
        for col in range(n_cols):
            for row in range(n_rows):
                th2.SetBinContent(col + 1, row + 1, grid[row][col])
        return th2

    def do_plot(self):
        c = ROOT.TCanvas('','',600,600)
        c.SetFillStyle(4000)
        c.SetFrameFillStyle(1000)
        c.SetFrameFillColor(0)
        self.data.Draw('COLZ')
        c.Print('%s/%s.pdf' %(self.config.get('General','plotpath'),self.name))
