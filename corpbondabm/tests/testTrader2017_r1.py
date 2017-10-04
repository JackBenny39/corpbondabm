import unittest

import numpy as np

from corpbondabm.trader2017_r1 import BuySide, MutualFund, InsuranceCo, HedgeFund
from corpbondabm.bondmarket2017_r1 import BondMarket

MM_FRACTION = 0.15


class TestTrader(unittest.TestCase):


    def setUp(self):
        self.b1 = BuySide('b1')
        self.m1 = MutualFund('m1', 0.03, 0.08)
        self.i1 = InsuranceCo('i1')
        self.h1 = HedgeFund('h1')
        
        self.bondmarket = BondMarket('bondmarket1')
        self.bondmarket.add_bond('MM101', 500, 1, .0175, .015, 2)
        self.bondmarket.add_bond('MM102', 500, 2, .025, .0175, 2)
        self.bondmarket.add_bond('MM103', 1000, 5, .0225, .025, 2)
        self.bondmarket.add_bond('MM104', 2000, 10, .024, .026, 2)
        self.bondmarket.add_bond('MM105', 1000, 25, .04, .0421, 2)
        
        for bond in self.bondmarket.bonds:
            mm_bond = {'Name': bond['Name'], 'Nominal': MM_FRACTION*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            self.m1.portfolio.append(mm_bond)
        
    def test_repr_BuySide(self):
        self.assertEqual('BuySide(b1)', '{0}'.format(self.b1))

    def test_repr_MutualFund(self):
        self.assertEqual('BuySide(m1, MutualFund)', '{0}'.format(self.m1))
        
    def test_add_nav_to_history(self):
        self.assertFalse(self.m1.nav_history)
        self.m1.add_nav_to_history(1)
        self.assertDictEqual(self.m1.nav_history, {1: 750})
        
    def test_compute_portfolio_value(self):
        portfolio_value = self.m1.compute_portfolio_value()
        bond_values = np.sum([x['Nominal'] for x in self.bondmarket.bonds])
        expected = MM_FRACTION*bond_values
        self.assertEqual(portfolio_value, expected)
          
    def test_compute_flow(self):
        self.m1.nav_history[1] = 100
        self.m1.nav_history[5] = 100
        self.m1.nav_history[6] = 101
        flow = self.m1.compute_flow(7)
        self.assertAlmostEqual(flow, 1.1888, 4)
        self.m1.nav_history[1] = 100
        self.m1.nav_history[5] = 100
        self.m1.nav_history[6] = 95
        flow = self.m1.compute_flow(7)
        self.assertAlmostEqual(flow, -5.492, 4)
        
    def test_make_rfq(self):
        rfq = self.m1.make_rfq('MM101', 'sell', 1000)
        expected = {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 1000}
        self.assertDictEqual(rfq, expected)
        
        
    def test_repr_InsuranceCo(self):
        self.assertEqual('BuySide(i1, InsuranceCo)', '{0}'.format(self.i1))
        
    def test_repr_HedgeFund(self):
        self.assertEqual('BuySide(h1, HedgeFund)', '{0}'.format(self.h1))