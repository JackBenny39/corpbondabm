import unittest

import numpy as np

from corpbondabm.trader2017_r1 import BuySide, MutualFund, InsuranceCo, HedgeFund, Dealer
from corpbondabm.bondmarket2017_r1 import BondMarket

MM_FRACTION = 0.15
IC_EQUITY = 0.4
TREYNOR_BOUNDS = [0.01, 0.0125]


class TestTrader(unittest.TestCase):


    def setUp(self):
        self.bondmarket = BondMarket('bondmarket1')
        self.bondmarket.add_bond('MM101', 500, 1, .0175, .015, 2)
        self.bondmarket.add_bond('MM102', 500, 2, .025, .0175, 2)
        self.bondmarket.add_bond('MM103', 1000, 5, .0225, .025, 2)
        self.bondmarket.add_bond('MM104', 2000, 10, .024, .026, 2)
        self.bondmarket.add_bond('MM105', 1000, 25, .04, .0421, 2)
        index_weights = self.bondmarket.compute_weights_from_nominal()
        bond_list = []
        mm_portfolio = {}
        ic_portfolio = {}
        d_portfolio = {}
        d_special = {'MM101': 0.9, 'MM102': 0.9, 'MM103': 0.75, 'MM104': 0.5, 'MM105': 0.5}
        for bond in self.bondmarket.bonds:
            mm_bond = {'Name': bond['Name'], 'Nominal': MM_FRACTION*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            ic_bond = {'Name': bond['Name'], 'Nominal': (1-MM_FRACTION)*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            d_bond = {'Name': bond['Name'], 'Nominal': bond['Nominal'], 'Price': bond['Price'], 'Specialization': d_special[bond['Name']]}
            bond_list.append(bond['Name'])
            mm_portfolio[bond['Name']] = mm_bond
            ic_portfolio[bond['Name']] = ic_bond
            d_portfolio[bond['Name']] = d_bond
            
        self.b1 = BuySide('b1', bond_list, mm_portfolio)
            
        self.m1 = MutualFund('m1', 0.03, 0.08, 0.05, bond_list, mm_portfolio, index_weights)
        prices = {k:self.m1.portfolio[k]['Price'] for k in self.m1.bond_list}
        bond_value = self.m1.compute_portfolio_value(prices)
        self.m1.cash = self.m1.target*bond_value/(1-self.m1.target)
        self.m1.add_nav_to_history(0, prices)
        
        self.i1 = InsuranceCo('i1', 1-IC_EQUITY, bond_list, ic_portfolio, 2003)
        prices = {k:self.i1.portfolio[k]['Price'] for k in self.i1.bond_list}
        bond_value = self.i1.compute_portfolio_value(prices)
        self.i1.equity = IC_EQUITY*bond_value/(1-IC_EQUITY)
        
        self.h1 = HedgeFund('h1', bond_list, mm_portfolio) # use MF portfolio for now
        
        self.d1 = Dealer('d1', bond_list, d_portfolio, 0.1, 0.075, TREYNOR_BOUNDS)
        
        
    def test_repr_BuySide(self):
        self.assertEqual('BuySide(b1)', '{0}'.format(self.b1))
        
    def test_make_rfq(self):
        self.m1.make_rfq('MM101', 'sell', 10)
        expected = {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 10}
        self.assertDictEqual(self.m1.rfq_collector[0], expected)
        
    def test_compute_portfolio_value(self):
        prices = {'MM101': 100, 'MM102': 100, 'MM103': 100, 'MM104': 100, 'MM105': 100}
        portfolio_value = self.m1.compute_portfolio_value(prices)
        bond_values = np.sum([x['Nominal'] for x in self.bondmarket.bonds])
        expected = MM_FRACTION*bond_values
        self.assertEqual(portfolio_value, expected)

    
    def test_repr_MutualFund(self):
        self.assertEqual('BuySide(m1, MutualFund)', '{0}'.format(self.m1))
        
    def test_add_nav_to_history(self):
        self.m1.nav_history = {}
        prices = {'MM101': 100, 'MM102': 100, 'MM103': 100, 'MM104': 100, 'MM105': 100}
        self.m1.add_nav_to_history(1, prices)
        self.assertDictEqual(self.m1.nav_history, {1: 788.91782200258319})
          
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
        
    def test_modify_portfolioMM(self):
        self.m1.cash = 0
        confirm_sell = {'Bond': 'MM101', 'Side': 'sell', 'Price': 100, 'Size': 5, 'BuySide': 'm1'}
        confirm_buy = {'Bond': 'MM105', 'Side': 'buy', 'Price': 100, 'Size': 10, 'BuySide': 'm1'}
        self.assertEqual(self.m1.cash, 0)
        self.m1.modify_portfolio(confirm_sell)
        self.assertEqual(self.m1.cash, 500)
        self.assertEqual(self.m1.portfolio['MM101']['Nominal'], 70)
        self.m1.modify_portfolio(confirm_buy)
        self.assertEqual(self.m1.cash, -500)
        self.assertEqual(self.m1.portfolio['MM105']['Nominal'], 160)
        
    def test_make_portfolio_decisionMF(self):
        prices = {'MM101': 101, 'MM102': 98, 'MM103': 95, 'MM104': 105, 'MM105': 100}
        # Do nothing: index doesn't change cash between limits
        self.m1.nav_history[1] = 750
        self.m1.nav_history[5] = 750
        self.m1.nav_history[6] = 750
        self.m1.cash = 30
        self.m1.portfolio['MM101']['Nominal'] = 73
        self.m1.portfolio['MM102']['Nominal'] = 72
        self.m1.portfolio['MM103']['Nominal'] = 145
        self.m1.portfolio['MM104']['Nominal'] = 285
        self.m1.portfolio['MM105']['Nominal'] = 137.5
        self.m1.make_portfolio_decision(7, prices)
        self.assertFalse(self.m1.rfq_collector)
        # Sell some: index decline, low on cash
        self.m1.nav_history[1] = 750
        self.m1.nav_history[5] = 750
        self.m1.nav_history[6] = 737.5
        self.m1.cash = 25
        self.m1.portfolio['MM101']['Nominal'] = 73
        self.m1.portfolio['MM102']['Nominal'] = 72
        self.m1.portfolio['MM103']['Nominal'] = 145
        self.m1.portfolio['MM104']['Nominal'] = 285
        self.m1.portfolio['MM105']['Nominal'] = 137.5
        self.m1.make_portfolio_decision(7, prices)
        expected = [
                    {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 2.0},
                    {'order_id': 'm1_2', 'name': 'MM102', 'side': 'sell', 'amount': 1.0},
                    {'order_id': 'm1_3', 'name': 'MM103', 'side': 'sell', 'amount': 3.0},
                    {'order_id': 'm1_4', 'name': 'MM104', 'side': 'sell', 'amount': 4.0}
                    ]
        for i in range(len(self.m1.rfq_collector)):
            with self.subTest(i=i):
                self.assertDictEqual(self.m1.rfq_collector[i], expected[i])
        # Buy some: index increase, extra cash
        self.m1.nav_history[1] = 750
        self.m1.nav_history[5] = 750
        self.m1.nav_history[6] = 767.5
        self.m1.cash = 50
        self.m1.portfolio['MM101']['Nominal'] = 68
        self.m1.portfolio['MM102']['Nominal'] = 79
        self.m1.portfolio['MM103']['Nominal'] = 138
        self.m1.portfolio['MM104']['Nominal'] = 293
        self.m1.portfolio['MM105']['Nominal'] = 139.5
        self.m1.make_portfolio_decision(7, prices)
        expected = [
                    {'order_id': 'm1_5', 'name': 'MM101', 'side': 'buy', 'amount': 6.0},
                    {'order_id': 'm1_6', 'name': 'MM103', 'side': 'buy', 'amount': 10.0},
                    {'order_id': 'm1_7', 'name': 'MM104', 'side': 'buy', 'amount': 6.0},
                    {'order_id': 'm1_8', 'name': 'MM105', 'side': 'buy', 'amount': 9.0}
                    ]
        for i in range(len(self.m1.rfq_collector)):
            with self.subTest(i=i):
                self.assertDictEqual(self.m1.rfq_collector[i], expected[i])
        
        
    def test_repr_InsuranceCo(self):
        self.assertEqual('BuySide(i1, InsuranceCo)', '{0}'.format(self.i1))
        
    def test_modify_portfolioIC(self):
        self.i1.equity = 0
        confirm_sell = {'Bond': 'MM101', 'Side': 'sell', 'Price': 100, 'Size': 5, 'BuySide': 'i1'}
        confirm_buy = {'Bond': 'MM105', 'Side': 'buy', 'Price': 100, 'Size': 10, 'BuySide': 'i1'}
        self.assertEqual(self.i1.equity, 0)
        self.i1.modify_portfolio(confirm_sell)
        self.assertEqual(self.i1.equity, 500)
        self.assertEqual(self.i1.portfolio['MM101']['Nominal'], 420)
        self.i1.modify_portfolio(confirm_buy)
        self.assertEqual(self.i1.equity, -500)
        self.assertEqual(self.i1.portfolio['MM105']['Nominal'], 860)
        
    def test_make_portfolio_decisionIC(self):
        prices = {'MM101': 101, 'MM102': 98, 'MM103': 95, 'MM104': 105, 'MM105': 100}
        self.i1.equity_returns[0] = 0.02
        np.random.seed(1) # randomly selects 'MM104'
        self.i1.make_portfolio_decision(1, prices)
        expected = {'order_id': 'i1_1', 'name': 'MM104', 'side': 'sell', 'amount': 5.0}
        self.assertDictEqual(self.i1.rfq_collector[0], expected)
        
   
    def test_repr_HedgeFund(self):
        self.assertEqual('BuySide(h1, HedgeFund)', '{0}'.format(self.h1))
        
        
    def test_repr_Dealer(self):
        self.assertEqual('Dealer(d1, Dealer)', '{0}'.format(self.d1))
        
    def test_update_limits(self):
        expected = {'MM101': {'Name': 'MM101', 'Nominal': 500, 'Price': 100.24721536368058, 'Specialization': 0.9, 'LowerLimit': -37.5, 'UpperLimit': 50.0, 'Quantity': 0}, 
                    'MM102': {'Name': 'MM102', 'Nominal': 500, 'Price': 101.46775304752784, 'Specialization': 0.9, 'LowerLimit': -37.5, 'UpperLimit': 50.0, 'Quantity': 0}, 
                    'MM103': {'Name': 'MM103', 'Nominal': 1000, 'Price': 98.83180926153969, 'Specialization': 0.75, 'LowerLimit': -75.0, 'UpperLimit': 100.0, 'Quantity': 0}, 
                    'MM104': {'Name': 'MM104', 'Nominal': 2000, 'Price': 98.24880431930488, 'Specialization': 0.5, 'LowerLimit': -150.0, 'UpperLimit': 200.0, 'Quantity': 0}, 
                    'MM105': {'Name': 'MM105', 'Nominal': 1000, 'Price': 96.7721765936335, 'Specialization': 0.5, 'LowerLimit': -75.0, 'UpperLimit': 100.0, 'Quantity': 0}}
        self.assertDictEqual(self.d1.portfolio, expected)
        
    def test_make_quote(self):
        '''
        There are 6 possibilities:
        1. rfq size results in a breach of the inventory limit (2 ways to do this)
        2. rfq is a buy (dealer quotes ask price) that results in positive inventory: bid set to scale, ask set by a fixed spread
        3. rfq is a buy (dealer quotes ask price) that results in negative inventory: ask set to scale
        4. rfq is a sell (dealer quotes bid price) that results in positive inventory: bid set to scale
        5. rfq is a sell  (dealer quotes bid price) that results in negative inventory: ask set to scale, bid set by a fixed spread
        6. rfq results in flat (zero) inventory: bid and ask set at a fixed symmetric spread around last trade price
        
        '''
        #1a: breach upper limit
        self.d1.portfolio['MM101']['Quantity'] = 48
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': None, 'side': 'sell', 'price': None}
        self.assertDictEqual(quote, expected)
        #1b: breach lower limit
        self.d1.portfolio['MM101']['Quantity'] = -35
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'buy', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': None, 'side': 'buy', 'price': None}
        self.assertDictEqual(quote, expected)
        #2
        self.d1.portfolio['MM101']['Quantity'] = 20
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'buy', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'buy', 'price': 100.23131901953005}
        self.assertDictEqual(quote, expected)
        #3
        self.d1.portfolio['MM101']['Quantity'] = -10
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'buy', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'buy', 'price': 100.70334019358533}
        self.assertDictEqual(quote, expected)
        #4
        self.d1.portfolio['MM101']['Quantity'] = 20
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'sell', 'price': 99.79109053377583}
        self.assertDictEqual(quote, expected)
        #5
        self.d1.portfolio['MM101']['Quantity'] = -10
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'sell', 'price': 100.1414784198565}
        self.assertDictEqual(quote, expected)
        #6
        self.d1.portfolio['MM101']['Quantity'] = -5
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'sell', 'price': 100.11832608678442}
        self.assertDictEqual(quote, expected)
        self.d1.portfolio['MM101']['Quantity'] = 5
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'buy', 'amount': 5}
        quote = self.d1.make_quote(rfq)
        expected = {'Dealer': 'd1', 'order_id': 'm1_1', 'name': 'MM101', 'amount': 5, 'side': 'buy', 'price': 100.37610464057674}
        self.assertDictEqual(quote, expected)
        # And finally, prices should fall with rising inventory
        self.d1.portfolio['MM101']['Quantity'] = -30
        rfq =  {'order_id': 'm1_1', 'name': 'MM101', 'side': 'sell', 'amount': 10}
        quote1 = self.d1.make_quote(rfq)
        price1 = quote1['price']
        self.d1.portfolio['MM101']['Quantity'] = -20
        rfq =  {'order_id': 'm1_2', 'name': 'MM101', 'side': 'sell', 'amount': 10}
        quote2 = self.d1.make_quote(rfq)
        price2 = quote2['price']
        self.assertLess(price2, price1)
        self.d1.portfolio['MM101']['Quantity'] = -10
        rfq =  {'order_id': 'm1_3', 'name': 'MM101', 'side': 'sell', 'amount': 10}
        quote3 = self.d1.make_quote(rfq)
        price3 = quote3['price']
        self.assertLess(price3, price2)
        self.d1.portfolio['MM101']['Quantity'] = 0
        rfq =  {'order_id': 'm1_4', 'name': 'MM101', 'side': 'sell', 'amount': 10}
        quote4 = self.d1.make_quote(rfq)
        price4 = quote4['price']
        self.assertLess(price4, price3)
        self.d1.portfolio['MM101']['Quantity'] = 10
        rfq =  {'order_id': 'm1_4', 'name': 'MM101', 'side': 'sell', 'amount': 20}
        quote5 = self.d1.make_quote(rfq)
        price5 = quote5['price']
        self.assertLess(price5, price4)

        
        