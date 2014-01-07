import ROOT

class PxarGui( ROOT.TGMainFrame ):
    def __init__( self, parent, width, height ):
       self.previous = ROOT.TPyDispatcher( self.draw_previous )
       self.forward = ROOT.TPyDispatcher( self.draw_next )
       ROOT.TGMainFrame.__init__( self, parent, width, height )

       self.Canvas    = ROOT.TRootEmbeddedCanvas( 'Canvas', self,800, 800 )
       self.AddFrame( self.Canvas, ROOT.TGLayoutHints() )
       self.ButtonsFrame = ROOT.TGHorizontalFrame( self, 200, 40 )

       self.DrawButton   = ROOT.TGTextButton( self.ButtonsFrame, '&Back', 10 )
       self.DrawButton.Connect( 'Clicked()', "TPyDispatcher", self.previous, 'Dispatch()' )
       self.ButtonsFrame.AddFrame( self.DrawButton, ROOT.TGLayoutHints() )

       self.DrawButton   = ROOT.TGTextButton( self.ButtonsFrame, '&Next', 10 )
       self.DrawButton.Connect( 'Clicked()', "TPyDispatcher", self.forward, 'Dispatch()' )
       self.ButtonsFrame.AddFrame( self.DrawButton, ROOT.TGLayoutHints() )

       #self.ComboFrame.AddFrame( self.ButtonsFrame, ROOT.TGLayoutHints() )
       self.combo = ROOT.TGComboBox(self.ButtonsFrame)
       l = ['a','b']
       for i in range(len(l)):
          self.combo.AddEntry(l[i],i+1)
       self.combo.Select(1)
       self.ButtonsFrame.AddFrame( self.combo, ROOT.TGLayoutHints() )
       self.combo.Resize(100,20)

       self.AddFrame(self.ButtonsFrame, ROOT.TGLayoutHints() )


       self.SetWindowName( 'pyXar' )
       self.MapSubwindows()
       self.Resize( self.GetDefaultSize() )
       #self.SetWMPosition(1000,1000)
       self.MapWindow()
       self.histos = [] 
       self.pos = 0

    def __del__(self):
       self.Cleanup()

    def update_window(self):
        '''Just draw what is in the self._histos[self.pos]'''
        if not self.histos:
            return
        histo_type = type(self.histos[self.pos]) 
        if histo_type == ROOT.TH2F:
            self.histos[self.pos].Draw('COLZ')
        elif histo_type == ROOT.THStack:
            self.histos[self.pos].Draw('NOSTACK')
        else:
            self.histos[self.pos].Draw()
        ROOT.gPad.Update()
    
    def draw_previous(self):
        '''Foward one position'''
        self.pos -= 1
        if self.pos < 0:
            self.pos = 0
        btn = ROOT.BindObject( ROOT.gTQSender, ROOT.TGTextButton )
        if btn.WidgetId() == 10:
            self.update_window()

    def draw_next(self):
        '''Foward one position'''
        self.pos += 1
        if self.pos >= len(self.histos):
            self.pos = len(self.histos)-1
        btn = ROOT.BindObject( ROOT.gTQSender, ROOT.TGTextButton )
        if btn.WidgetId() == 10:
            self.update_window()
    
    def update(self):
        '''Always go to last position'''
        self.pos = len(self.histos)-1
        self.update_window()
