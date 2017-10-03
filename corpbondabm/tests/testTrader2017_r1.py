import unittest

from corpbondabm.trader2017_r1 import BuySide, MutualFund, InsuranceCo


class TestTrader(unittest.TestCase):


    def setUp(self):
        self.b1 = BuySide('b1')
        self.m1 = MutualFund('m1')
        self.i1 = InsuranceCo('i1')
        
    def test_repr_BuySide(self):
        self.assertEqual('BuySide(b1)', '{0}'.format(self.b1))

    def test_repr_MutualFund(self):
        self.assertEqual('BuySide(m1, MutualFund)', '{0}'.format(self.m1))
        
    def test_repr_InsuranceCo(self):
        print(self.i1)
        self.assertEqual('BuySide(i1, InsuranceCo)', '{0}'.format(self.i1))