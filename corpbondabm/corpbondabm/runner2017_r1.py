import time

import numpy as np
#import pandas as pd

from corpbondabm.bondmarket2017_r1 import BondMarket
from corpbondabm.trader2017_r1 import MutualFund, InsuranceCo, Dealer

TREYNOR_BOUNDS = [0.01, 0.0125]

class Runner(object):
    
    def __init__(self, market_name='bondmarket1', 
                 mm_name='m1', mm_share=0.15, mm_lower=0.03, mm_upper=0.08, mm_target=0.05,
                 ic_name='i1', ic_bond=0.6, dealer_long=0.1, dealer_short=0.075, run_steps=252,
                 year=2003):
        self.bondmarket = self.make_market(market_name)
        self.mutualfund = self.make_mutual_fund(mm_name, mm_share, mm_lower, mm_upper, mm_target)
        self.insuranceco = self.make_insurance_co(ic_name, 1-mm_share, ic_bond, year)
        self.dealers, self.dealers_dict = self.make_dealers(dealer_long, dealer_short)
        self.run_steps = run_steps
        
    def make_market(self, name):
        # allow user to specify as args?
        bondmarket = BondMarket(name)
        bondmarket.add_bond('MM101', 5000, 1, .0175, .015, 2)
        bondmarket.add_bond('MM102', 5000, 2, .025, .0175, 2)
        bondmarket.add_bond('MM103', 10000, 5, .0225, .025, 2)
        bondmarket.add_bond('MM104', 20000, 10, .024, .026, 2)
        bondmarket.add_bond('MM105', 10000, 25, .04, .0421, 2)
        return bondmarket
    
    def make_mutual_fund(self, name, share, ll, ul, target):
        nominal_weights = self.bondmarket.compute_weights_from_nominal()
        bond_list = []
        portfolio = {}
        for bond in self.bondmarket.bonds:
            bond_list.append(bond['Name'])
            mm_bond = {'Name': bond['Name'], 'Nominal': share*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            portfolio[bond['Name']] = mm_bond
        m1 = MutualFund(name, ll, ul, target, bond_list, portfolio, nominal_weights)
        bond_value = m1.compute_portfolio_value()
        m1.cash = target*bond_value/(1-target)
        m1.add_nav_to_history(0)
        return m1
        
    def make_insurance_co(self, name, share, bond_weight, year):
        bond_list = []
        portfolio = {}
        for bond in self.bondmarket.bonds:
            bond_list.append(bond['Name'])
            ic_bond = {'Name': bond['Name'], 'Nominal': share*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            portfolio[bond['Name']] = ic_bond
        i1 = InsuranceCo(name, bond_weight, bond_list, portfolio, year)
        bond_value = i1.compute_portfolio_value()
        i1.equity = (1-bond_weight)*bond_value/bond_weight
        return i1
    
    def make_dealer(self, name, special, long_limit, short_limit):
        bond_list = []
        portfolio = {}
        for bond in self.bondmarket.bonds:
            d_bond = {'Name': bond['Name'], 'Nominal': bond['Nominal'], 'Price': bond['Price'], 'Specialization': special[bond['Name']]}
            bond_list.append(bond['Name'])
            portfolio[bond['Name']] = d_bond
        return Dealer(name, bond_list, portfolio, long_limit, short_limit, TREYNOR_BOUNDS)
    
    def make_dealers(self, ul, ll):
        # maybe pass these in as args - along with bond setup
        d_special = {'d1': {'MM101': 0.9, 'MM102': 0.9, 'MM103': 0.75, 'MM104': 0.5, 'MM105': 0.5},
                     'd2': {'MM101': 0.5, 'MM102': 0.75, 'MM103': 0.9, 'MM104': 0.75, 'MM105': 0.5},
                     'd3': {'MM101': 0.5, 'MM102': 0.5, 'MM103': 0.75, 'MM104': 0.9, 'MM105': 0.9}}
        dealers = [self.make_dealer(name, special, ul, ll) for name, special in d_special.items()]
        dealers_dict = dict(zip(['d%i' % i for i in range(1, 4)], dealers))
        return dealers, dealers_dict
    
    def make_buyside(self):
        buyside = np.array([self.insuranceco, self.mutualfund])
        np.random.shuffle(buyside)
        return buyside

    def seed_mutual_fund(self, prime1):
        for current_date in range(prime1):
            self.mutualfund.update_prices(self.bondmarket.last_prices)
            self.mutualfund.add_nav_to_history(current_date)
            
    def run_mcs(self, prime1):
        prices = self.bondmarket.last_prices
        print(prime1-1, prices)
        for current_date in range(prime1, prime1+self.run_steps):
            for buyside in self.make_buyside():
                buyside.make_portfolio_decision(current_date)
                if buyside.rfq_collector:
                    for rfq in buyside.rfq_collector:
                        quotes = [d.make_quote(rfq) for d in self.dealers]
                        # Note: selected dealer and buyside know the new price
                        if any(quotes):
                            dealer_confirm, buyside_confirm = self.bondmarket.match_trade(quotes, current_date)
                            self.dealers_dict[dealer_confirm['Dealer']].modify_portfolio(dealer_confirm)
                            buyside.modify_portfolio(buyside_confirm)
                            print(current_date, buyside_confirm)
            # All agents get price updates from the bondmarket at the end of the day
            prices = self.bondmarket.last_prices
            for d in self.dealers:
                d.update_prices(prices)
            self.mutualfund.update_prices(prices)
            self.mutualfund.add_nav_to_history(current_date)
            self.insuranceco.update_prices(prices)
            print(current_date, prices)
            print(current_date, self.mutualfund.nav_history[current_date])

                    
                        
        
        
if __name__ == '__main__':
    
    start = time.time()
    print(start)
    #market_name = 'bondmarket1'
    #mutualfund_name = 'm1' 
    mm_share = 0.15
    #mm_lower = 0.03
    #mm_upper = 0.08
    #mm_target = 0.05
    #ic_name='i1'
    #ic_bond=0.6
    #dealer_long=0.1
    #dealer_short=0.075
    run_steps=12
    #year=2003
    
    market1 = Runner(mm_share=mm_share, run_steps=run_steps)
    market1.seed_mutual_fund(8)
    market1.run_mcs(8)


