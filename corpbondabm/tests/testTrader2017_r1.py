import unittest

import numpy as np

from corpbondabm.trader2017_r1 import BuySide, MutualFund, InsuranceCo, HedgeFund
from corpbondabm.bondmarket2017_r1 import BondMarket

MM_FRACTION = 0.15


class TestTrader(unittest.TestCase):


    def setUp(self):
        self.b1 = BuySide('b1')
        self.m1 = MutualFund('m1', 0.03, 0.08, 0.05)
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
            self.m1.bond_list.append(bond['Name'])
            self.m1.portfolio[bond['Name']] = mm_bond
        prices = {k:self.m1.portfolio[k]['Price'] for k in self.m1.bond_list}
        bond_value = self.m1.compute_portfolio_value(prices)
        self.m1.cash = self.m1.target*bond_value/(1-self.m1.target)
        self.m1.index_weights = self.bondmarket.compute_weights_from_nominal()
        self.m1.add_nav_to_history(0, prices)
        
    def test_repr_BuySide(self):
        self.assertEqual('BuySide(b1)', '{0}'.format(self.b1))

    def test_repr_MutualFund(self):
        self.assertEqual('BuySide(m1, MutualFund)', '{0}'.format(self.m1))
        
    def test_add_nav_to_history(self):
        self.m1.nav_history = {}
        prices = {'MM101': 100, 'MM102': 100, 'MM103': 100, 'MM104': 100, 'MM105': 100}
        self.m1.add_nav_to_history(1, prices)
        self.assertDictEqual(self.m1.nav_history, {1: 788.91782200258319})
        
    def test_compute_portfolio_value(self):
        prices = {'MM101': 100, 'MM102': 100, 'MM103': 100, 'MM104': 100, 'MM105': 100}
        portfolio_value = self.m1.compute_portfolio_value(prices)
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
        self.m1.make_rfq('MM101', 'sell', 10)
        expected = {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 10}
        self.assertDictEqual(self.m1.rfq_collector[0], expected)
        
    def test_modify_portfolio(self):
        self.m1.cash = 0
        confirm_sell = {'name': 'MM101', 'side': 'sell', 'price': 100, 'size': 5}
        confirm_buy = {'name': 'MM105', 'side': 'buy', 'price': 100, 'size': 10}
        self.assertEqual(self.m1.cash, 0)
        self.m1.modify_portfolio(confirm_sell)
        self.assertEqual(self.m1.cash, 500)
        self.assertEqual(self.m1.portfolio['MM101']['Nominal'], 70)
        self.m1.modify_portfolio(confirm_buy)
        self.assertEqual(self.m1.cash, -500)
        self.assertEqual(self.m1.portfolio['MM105']['Nominal'], 160)
        
    def test_make_portfolio_decision(self):
        # Sell some: index decline, low on cash
        self.m1.nav_history[1] = 750
        self.m1.nav_history[5] = 750
        self.m1.nav_history[6] = 712.5
        self.m1.cash = 22
        self.m1.portfolio['MM101']['Nominal'] = 73
        self.m1.portfolio['MM102']['Nominal'] = 72
        self.m1.portfolio['MM103']['Nominal'] = 145
        self.m1.portfolio['MM104']['Nominal'] = 285
        self.m1.portfolio['MM105']['Nominal'] = 137.5
        self.m1.make_portfolio_decision(7)
        self.assertDictEqual(self.m1.rfq_collector[0], {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 1})
        self.assertDictEqual(self.m1.rfq_collector[1], {'order_id': 'm1_2', 'name': 'MM103', 'side': 'sell', 'amount': 2})
        print(self.m1.rfq_collector)
        
        self.m1.nav_history[1] = 750
        self.m1.nav_history[5] = 750
        self.m1.nav_history[6] = 787.5
        self.m1.cash = 62
        self.m1.portfolio['MM101']['Nominal'] = 73
        self.m1.portfolio['MM102']['Nominal'] = 72
        self.m1.portfolio['MM103']['Nominal'] = 145
        self.m1.portfolio['MM104']['Nominal'] = 285
        self.m1.portfolio['MM105']['Nominal'] = 140
        
        
        print(self.m1.rfq_collector)
        
        
    def test_repr_InsuranceCo(self):
        self.assertEqual('BuySide(i1, InsuranceCo)', '{0}'.format(self.i1))
        
    def test_repr_HedgeFund(self):
        self.assertEqual('BuySide(h1, HedgeFund)', '{0}'.format(self.h1))