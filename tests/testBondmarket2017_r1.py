import unittest

import numpy as np

from corpbondabm.bondmarket2017_r1 import BondMarket


class TestBondmarket(unittest.TestCase):


    def setUp(self):
        self.bondmarket = BondMarket('bondmarket1', 2003)
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
        self.assertEqual(self.bondmarket.last_prices['MM101'], price1)
        price2 = 101.46775304752784
        expected = {'Name': 'MM102', 'Nominal': 500, 'Maturity': 2, 'Coupon': .025, 'Yield': .0175, 'Price': price2}
        self.assertDictEqual(self.bondmarket.bonds[1], expected)
        self.assertEqual(self.bondmarket.last_prices['MM102'], price2)
        price3 = 98.83180926153969
        expected = {'Name': 'MM103', 'Nominal': 1000, 'Maturity': 5, 'Coupon': .0225, 'Yield': .025, 'Price': price3}
        self.assertDictEqual(self.bondmarket.bonds[2], expected)
        self.assertEqual(self.bondmarket.last_prices['MM103'], price3)
        price4 = 98.24880431930488
        expected = {'Name': 'MM104', 'Nominal': 2000, 'Maturity': 10, 'Coupon': .024, 'Yield': .026, 'Price': price4}
        self.assertDictEqual(self.bondmarket.bonds[3], expected)
        self.assertEqual(self.bondmarket.last_prices['MM104'], price4)
        price5 = 96.7721765936335
        expected = {'Name': 'MM105', 'Nominal': 1000, 'Maturity': 25, 'Coupon': .04, 'Yield': .0421, 'Price': price5}
        self.assertDictEqual(self.bondmarket.bonds[4], expected)
        self.assertEqual(self.bondmarket.last_prices['MM105'], price5)
        
    def test_compute_weights_from_price(self):
        weights = list(np.round(self.bondmarket.compute_weights_from_price(),2))
        expected = [0.1, 0.1, 0.2, 0.4, 0.2]
        self.assertListEqual(weights, expected)
        
    def test_compute_weights_from_nominal(self):
        weights = self.bondmarket.compute_weights_from_nominal()
        expected = {'MM101': 0.1, 'MM102': 0.1, 'MM103': 0.2, 'MM104': 0.4, 'MM105': 0.2}
        self.assertDictEqual(weights, expected)
        
    def test_report_trades(self):
        self.assertFalse(self.bondmarket.trades)
        matcher = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 20, 'side': 'buy', 'price': 99.95}
        trade_report = {'Sequence': 1, 'Dealer': 'd1', 'OrderId': 'm1_1', 'Bond': 'MM101', 'Size': 20, 'Side': 'buy', 
                        'Price': 99.95, 'Day': 1}
        self.bondmarket.report_trades(matcher, 1)
        self.assertDictEqual(self.bondmarket.trades[0], trade_report)
        self.assertEqual(self.bondmarket.last_prices['MM101'], 99.95)
        
    def test_match_trade(self):
        quotes = [
                    {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'buy', 'price': 100.1183},
                    {'Dealer': 'd2', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'buy', 'price': 100.1453},
                    {'Dealer': 'd3', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'buy', 'price': 100.1183}
                ]
        step = 10
        np.random.seed(1) # randomly selects position 1 (d3)
        dealer_confirm, buyside_confirm = self.bondmarket.match_trade(quotes, step)
        self.assertDictEqual({'Dealer': 'd3', 'Size': 5, 'Bond': 'MM101', 'Side': 'buy', 'Price': 100.1183}, dealer_confirm)
        self.assertDictEqual({'BuySide': 'm1', 'Size': 5, 'Bond': 'MM101', 'Side': 'buy', 'Price': 100.1183}, buyside_confirm)
        
        quotes = [
                    {'Dealer': 'd1', 'order_id': 'm1_2', 'name': 'MM101', 'amount': 8, 'side': 'sell', 'price': 99.6789},
                    {'Dealer': 'd2', 'order_id': 'm1_2', 'name': 'MM101', 'amount': 8, 'side': 'sell', 'price': 99.8888},
                    {'Dealer': 'd3', 'order_id': 'm1_2', 'name': 'MM101', 'amount': 8, 'side': 'sell', 'price': 99.8888}
                ]
        step = 11
        np.random.seed(2) # randomly selects position 0 (d2)
        dealer_confirm, buyside_confirm = self.bondmarket.match_trade(quotes, step)
        self.assertDictEqual({'Dealer': 'd2', 'Size': 8, 'Bond': 'MM101', 'Side': 'sell', 'Price': 99.8888}, dealer_confirm)
        self.assertDictEqual({'BuySide': 'm1', 'Size': 8, 'Bond': 'MM101', 'Side': 'sell', 'Price': 99.8888}, buyside_confirm)
      
    def test_update_eod_bond_price(self):
        for bond in self.bondmarket.bonds:
            self.bondmarket.last_prices[bond['Name']] += 1.0
        self.bondmarket.update_eod_bond_price(8)
        new_bondmarket_prices = np.array(list(self.bondmarket.last_prices.values()))
        updated_bondmarket_prices = np.array([bond['Price'] for bond in self.bondmarket.bonds])
        expected_prices = np.array([101.24725089, 102.468441831, 99.8341791171, 99.2514299988, 97.7771024019])
        for i in range(5):
            with self.subTest(i=i):
                self.assertAlmostEqual(new_bondmarket_prices[i], expected_prices[i], 6)
                self.assertAlmostEqual(updated_bondmarket_prices[i], expected_prices[i], 6)
                
    def test_shock_ytm(self):
        old_rates = np.array([bond['Yield'] for bond in self.bondmarket.bonds])
        self.bondmarket.shock_ytm(0.01)
        new_rates = np.array([bond['Yield'] for bond in self.bondmarket.bonds])
        diff_rates = new_rates - (old_rates + 0.01)
        self.assertFalse(diff_rates.all())
    
              
        
        
