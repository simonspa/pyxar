import ROOT
import numpy
import array

class Plotter(object):

    def __init__(self, config, test):
        self.config = config
        self.name = test.name
        self._histos = [self.matrix_to_th2(result['data'], result['title'], result['x_title'], result['y_title']) for result in test.results]
    
    @property
    def histos(self):
        return self._histos

    @staticmethod
    def create_th1(data, name, x_title, y_title, minimum = None, maximum = None):
        if not maximum:
            maximum = int(numpy.amax(data))
        if not minimum:
            minimum = int(numpy.nanmin(data))
        th1 = ROOT.TH1F(name, name, int(maximum-minimum), minimum, maximum)
        th1.SetDirectory(0)
        th1.GetXaxis().SetTitle(x_title)
        th1.GetYaxis().SetTitle(y_title)
        th1.SetDrawOption('HIST')
        th1.SetLineWidth(2)
        for entry in data.flatten():
            th1.Fill(entry)
        return th1
        
    @staticmethod
    def create_tgraph(data, name, x_title, y_title, minimum = None, maximum = None):
        xdata = list(xrange(len(data)))
        x = array.array('d', xdata)
        y = array.array('d', data)
        gr = ROOT.TGraph(len(x),x,y)
        #gr.SetDirectory(0)
        gr.SetTitle(name)
        gr.SetLineColor(4)
        gr.SetMarkerColor(4)
        gr.SetMarkerSize(0.5)
        gr.SetMarkerStyle(21)
        gr.GetXaxis().SetTitle(x_title)
        gr.GetYaxis().SetTitle(y_title)
        gr.SetDrawOption('Acp')
        gr.SetLineWidth(2)
        return gr

    @staticmethod
    def create_tgraph2(data, name, x_title, y_title, minimum = None, maximum = None, step = 1, start = 0):
        xdata = range(start, start + step*len(data),step)
        x = array.array('d', xdata)
        y = array.array('d', data)
        gr = ROOT.TGraph(len(x),x,y)
        #gr.SetDirectory(0)
        gr.SetTitle(name)
        gr.SetLineColor(4)
        gr.SetMarkerColor(4)
        gr.SetMarkerSize(0.5)
        gr.SetMarkerStyle(21)
        gr.GetXaxis().SetTitle(x_title)
        gr.GetYaxis().SetTitle(y_title)
        gr.SetDrawOption('Acp')
        gr.SetLineWidth(2)
        return gr


    @staticmethod
    def create_th2(data, len_x, len_y, name, x_title, y_title):
        th2 = ROOT.TH2F(name, name, len_x, 0, len_x , len_y, 0, len_y)
        th2.SetDirectory(0)
        th2.GetXaxis().SetTitle(x_title)
        th2.GetYaxis().SetTitle(y_title)
        th2.SetDrawOption('COLZ')
        for x in range(len_x):
            for y in range(len_y):
                th2.SetBinContent(x + 1, y + 1, data[x][y])
        return th2
 
    @staticmethod
    def create_th2_binned(data, len_x, xbins, len_y, ybins, name, x_title, y_title):
        th2 = ROOT.TH2F(name, name, xbins, 0, len_x , ybins, 0, len_y)
        th2.SetDirectory(0)
        th2.GetXaxis().SetTitle(x_title)
        th2.GetYaxis().SetTitle(y_title)
        th2.SetDrawOption('COLZ')
        for x in range(xbins):
            for y in range(ybins):
                th2.SetBinContent(x + 1, y + 1, data[x][y])
        return th2
    
    def matrix_to_th2(self, matrix, name, x_title, y_title):
        dim = matrix.shape
        return self.create_th2(matrix, dim[0], dim[1], name, x_title, y_title)
