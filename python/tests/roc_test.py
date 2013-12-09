import unittest
from copy import deepcopy
from python import Roc
from python import BetterConfigParser

class TestRoc(unittest.TestCase):

    def test_n_pixel(self):
        """Tests n pixels"""
        config = BetterConfigParser()
        config.read('data/roc')
        roc = Roc(config)
        self.assertEqual(4160,roc.n_pixels)
    
    def test_trim_bits(self):
        """Tests if trim bits are correct"""
        config = BetterConfigParser()
        config.read('data/roc')
        roc = Roc(config)
        self.assertEqual([15] * roc.n_pixels, roc.trim_bits)

if __name__ == '__main__': 
    unittest.main()
