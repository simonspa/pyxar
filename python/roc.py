class Roc(object):

    def __init__(self, config):
        """Initialize ROC (readout chip)."""
        self._num_rows = int(config.get('ROC','rows'))
        self._num_cols = int(config.get('ROC','cols'))
        self._num_pixels = self._num_rows*self._num_cols
        self._trim_bits = [15] * self._num_pixels 

    @property
    def n_rows(self):
        """Get number of rows."""
        return self._num_rows

    @property
    def n_cols(self):
        """Get number of columns."""
        return self._num_cols
    
    @property
    def n_pixels(self):
        """Get number of pixels."""
        return self._num_pixels

    @property
    def trim_bits(self):
        """Get trim bits."""
        return self._trim_bits

