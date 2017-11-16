import time

import numpy as np

from corpbondabm.bondmarket2017_r1 import BondMarket
from corpbondabm.trader2017_r1 import MutualFund2, InsuranceCo, Dealer

TREYNOR_BOUNDS = [0.01, 0.0125]
TREYNOR_FACTOR = 10000
PRIMER = 8

BONDS = [
         {'Name': 'MM101', 'Nominal': 500000, 'Maturity': 1, 'Coupon': 0.0175, 'Yield': 0.015, 'NPer': 2},
         {'Name': 'MM102', 'Nominal': 500000, 'Maturity': 2, 'Coupon': 0.025, 'Yield': 0.0175, 'NPer': 2},
         {'Name': 'MM103', 'Nominal': 1000000, 'Maturity': 5, 'Coupon': 0.0225, 'Yield': 0.025, 'NPer': 2},
         {'Name': 'MM104', 'Nominal': 2000000, 'Maturity': 10, 'Coupon': 0.024, 'Yield': 0.026, 'NPer': 2},
         {'Name': 'MM105', 'Nominal': 1000000, 'Maturity': 25, 'Coupon': 0.04, 'Yield': 0.0421, 'NPer': 2}
        ]
    
D_SPECIAL = {
             'd1': {'MM101': 0.9, 'MM102': 0.9, 'MM103': 0.75, 'MM104': 0.5, 'MM105': 0.5},
             'd2': {'MM101': 0.5, 'MM102': 0.75, 'MM103': 0.9, 'MM104': 0.75, 'MM105': 0.5},
             'd3': {'MM101': 0.5, 'MM102': 0.5, 'MM103': 0.75, 'MM104': 0.9, 'MM105': 0.9}
            }

class Runner(object):
    
    def __init__(self, market_name='bondmarket1', bonds=BONDS, d_special=D_SPECIAL,
                 mm_name='m1', mm_share=0.15, mm_lower=0.03, mm_upper=0.07, mm_target=0.05,
                 ic_name='i1', ic_bond=0.6, dealer_long=0.1, dealer_short=0.075, run_steps=252,
                 year=2003, h5_file='test.h5'):
        self.bondmarket = self.make_market(market_name, year, bonds)
        self.mutualfund = self.make_mutual_fund(mm_name, mm_share, mm_lower, mm_upper, mm_target)
        self.insuranceco = self.make_insurance_co(ic_name, 1-mm_share, ic_bond, year)
        self.dealers, self.dealers_dict = self.make_dealers(dealer_long, dealer_short, d_special)
        self.run_steps = run_steps
        self.seed_mutual_fund(PRIMER)
        self.run_mcs(PRIMER)
        self.make_h5s(h5_file)
        
    def make_market(self, name, year, bonds):
        bondmarket = BondMarket(name, year)
        for bond in bonds:
            bondmarket.add_bond(bond['Name'], bond['Nominal'], bond['Maturity'], bond['Coupon'], bond['Yield'], bond['NPer'])
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
        m1 = MutualFund2(name, ll, ul, target, bond_list, portfolio, nominal_weights, 100000)
        return m1
        
    def make_insurance_co(self, name, share, bond_weight, year):
        bond_list = []
        portfolio = {}
        for bond in self.bondmarket.bonds:
            bond_list.append(bond['Name'])
            ic_bond = {'Name': bond['Name'], 'Nominal': share*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            portfolio[bond['Name']] = ic_bond
        i1 = InsuranceCo(name, 1-bond_weight, bond_list, portfolio, year)
        return i1
    
    def make_dealer(self, name, special, long_limit, short_limit):
        bond_list = []
        portfolio = {}
        for bond in self.bondmarket.bonds:
            d_bond = {'Name': bond['Name'], 'Nominal': bond['Nominal'], 'Price': bond['Price'], 'Specialization': special[bond['Name']]}
            bond_list.append(bond['Name'])
            portfolio[bond['Name']] = d_bond
        return Dealer(name, bond_list, portfolio, long_limit, short_limit, TREYNOR_BOUNDS, TREYNOR_FACTOR)
    
    def make_dealers(self, ul, ll, d_special):
        dealers = [self.make_dealer(name, special, ul, ll) for name, special in d_special.items()]
        dealers_dict = dict(zip(['d%i' % i for i in range(1, 4)], dealers))
        return dealers, dealers_dict
    
    def make_buyside(self):
        buyside = np.array([self.insuranceco, self.mutualfund])
        np.random.shuffle(buyside)
        #return buyside
        return [self.mutualfund]
    
    def make_h5s(self, h5_file):
        self.bondmarket.last_prices_to_h5(h5_file)
        self.bondmarket.trades_to_h5(h5_file)
        self.mutualfund.nav_to_h5(h5_file)
    
    def seed_mutual_fund(self, prime1):
        for current_date in range(prime1):
            self.mutualfund.update_prices(self.bondmarket.last_prices)
            self.mutualfund.add_nav_to_history(current_date)
            
    def run_mcs(self, prime1):
        prices = self.bondmarket.last_prices
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
            # All agents get price updates from the bondmarket at the end of the day
            self.bondmarket.update_eod_bond_price(current_date)
            if current_date == 50:
                self.bondmarket.shock_ytm(0.01)
            prices = self.bondmarket.last_prices
            for d in self.dealers:
                d.update_prices(prices)
            self.mutualfund.update_prices(prices)
            self.mutualfund.add_nav_to_history(current_date)
            self.insuranceco.update_prices(prices)
            self.bondmarket.print_last_prices(current_date)

                    
if __name__ == '__main__':
    
    start = time.time()
    print(start)
    #market_name = 'bondmarket1'
    #mutualfund_name = 'm1' 
    mm_share = 0.35
    #mm_lower = 0.03
    #mm_upper = 0.08
    #mm_target = 0.05
    #ic_name='i1'
    #ic_bond=0.6
    #dealer_long=0.1
    #dealer_short=0.075
    run_steps=240
    year=2016
        
    #bonds = [
            #{'Name': 'MM101', 'Nominal': 500000, 'Maturity': 1, 'Coupon': 0.0175, 'Yield': 0.015, 'NPer': 2},
            #{'Name': 'MM102', 'Nominal': 500000, 'Maturity': 2, 'Coupon': 0.025, 'Yield': 0.0175, 'NPer': 2},
            #{'Name': 'MM103', 'Nominal': 1000000, 'Maturity': 5, 'Coupon': 0.0225, 'Yield': 0.025, 'NPer': 2},
            #{'Name': 'MM104', 'Nominal': 2000000, 'Maturity': 10, 'Coupon': 0.024, 'Yield': 0.026, 'NPer': 2},
            #{'Name': 'MM105', 'Nominal': 1000000, 'Maturity': 25, 'Coupon': 0.04, 'Yield': 0.0421, 'NPer': 2}
            #]
    
    #d_special = {
                #'d1': {'MM101': 0.9, 'MM102': 0.9, 'MM103': 0.75, 'MM104': 0.5, 'MM105': 0.5},
                #'d2': {'MM101': 0.5, 'MM102': 0.75, 'MM103': 0.9, 'MM104': 0.75, 'MM105': 0.5},
                #'d3': {'MM101': 0.5, 'MM102': 0.5, 'MM103': 0.75, 'MM104': 0.9, 'MM105': 0.9}
                #}
    
    # Write output to h5 file
    h5filename = 'test.h5'
    h5dir = 'C:\\Users\\user\\Documents\\Agent-Based Models\\Corporate Bonds\\h5 files\\'
    h5_file = '%s%s' % (h5dir, h5filename)
    
    market1 = Runner(mm_share=mm_share, run_steps=run_steps, year=year, h5_file=h5_file)
    
    print('Run Time: %.2f seconds' % ((time.time() - start)))

    