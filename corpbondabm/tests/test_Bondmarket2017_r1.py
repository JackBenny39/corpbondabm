import unittest

import numpy as np

from corpbondabm.bondmarket2017_r1 import BondMarket


class TestTrader(unittest.TestCase):


    def setUp(self):
        self.bondmarket = BondMarket('bondmarket1')
        self.bondmarket.add_bond('MM101', 500, 1, .0175, .015, 2)
        self.bondmarket.add_bond('MM102', 500, 2, .025, .0175, 2)
        self.bondmarket.add_bond('MM103', 1000, 5, .0225, .025, 2)
        self.bondmarket.add_bond('MM104', 2000, 10, .024, .026, 2)
        self.bondmarket.add_bond('MM105', 1000, 25, .04, .0421, 2)
        
    def test_repr_BondMarket(self):
        self.assertEqual('BondMarket(bondmarket1)', '{0}'.format(self.bondmarket))
        
    def test_add_bond(self):
        # Also tests _price_bond()
        price1 = 100.24721536368058
        expected = {'Name': 'MM101', 'Nominal': 500, 'Maturity': 1, 'Coupon': .0175, 'Yield': .015, 'Price': price1}
        self.assertDictEqual(self.bondmarket.bonds[0], expected)
        price2 = 101.46775304752784
        expected = {'Name': 'MM102', 'Nominal': 500, 'Maturity': 2, 'Coupon': .025, 'Yield': .0175, 'Price': price2}
        self.assertDictEqual(self.bondmarket.bonds[1], expected)
        price3 = 98.83180926153969
        expected = {'Name': 'MM103', 'Nominal': 1000, 'Maturity': 5, 'Coupon': .0225, 'Yield': .025, 'Price': price3}
        self.assertDictEqual(self.bondmarket.bonds[2], expected)
        price4 = 98.24880431930487
        expected = {'Name': 'MM104', 'Nominal': 2000, 'Maturity': 10, 'Coupon': .024, 'Yield': .026, 'Price': price4}
        self.assertDictEqual(self.bondmarket.bonds[3], expected)
        price5 = 96.7721765936335
        expected = {'Name': 'MM105', 'Nominal': 1000, 'Maturity': 25, 'Coupon': .04, 'Yield': .0421, 'Price': price5}
        self.assertDictEqual(self.bondmarket.bonds[4], expected)
        
    def test_compute_weights_from_price(self):
        weights = list(np.round(self.bondmarket.compute_weights_from_price(),2))
        expected = [0.1, 0.1, 0.2, 0.4, 0.2]
        self.assertListEqual(weights, expected)
        
    def test_compute_weights_from_nominal(self):
        weights = self.bondmarket.compute_weights_from_nominal()
        expected = {'MM101': 0.1, 'MM102': 0.1, 'MM103': 0.2, 'MM104': 0.4, 'MM105': 0.2}
        self.assertDictEqual(weights, expected)
        
        