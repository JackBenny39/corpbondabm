import time

import numpy as np

from corpbondabm.bondmarket2017_r1 import BondMarket
from corpbondabm.trader2017_r1 import MutualFund, InsuranceCo

class Runner(object):
    
    def __init__(self, market_name='bondmarket1', 
                 mm_name='m1', mm_share=0.15, mm_lower=0.03, mm_upper=0.08, mm_target=0.05,
                 ic_name='i1', ic_bond=0.6):
        self.bondmarket = self.make_market(market_name)
        self.mutualfund = self.make_mutual_fund(mm_name, mm_share, mm_lower, mm_upper, mm_target)
        self.insuranceco = self.make_insurance_co(ic_name, 1-mm_share, ic_bond)
        
    def make_market(self, name):
        bondmarket = BondMarket(name)
        bondmarket.add_bond('MM101', 500, 1, .0175, .015, 2)
        bondmarket.add_bond('MM102', 500, 2, .025, .0175, 2)
        bondmarket.add_bond('MM103', 1000, 5, .0225, .025, 2)
        bondmarket.add_bond('MM104', 2000, 10, .024, .026, 2)
        bondmarket.add_bond('MM105', 1000, 25, .04, .0421, 2)
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
        prices = {k:m1.portfolio[k]['Price'] for k in m1.bond_list}
        bond_value = m1.compute_portfolio_value(prices)
        m1.cash = target*bond_value/(1-target)
        m1.add_nav_to_history(0, prices)
        return m1
        
    def make_insurance_co(self, name, share, bond_weight):
        bond_list = []
        portfolio = {}
        for bond in self.bondmarket.bonds:
            bond_list.append(bond['Name'])
            ic_bond = {'Name': bond['Name'], 'Nominal': share*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            portfolio[bond['Name']] = ic_bond
        i1 = InsuranceCo(name, bond_weight, bond_list, portfolio)
        prices = {k:i1.portfolio[k]['Price'] for k in i1.bond_list}
        bond_value = i1.compute_portfolio_value(prices)
        i1.equity = (1-bond_weight)*bond_value/bond_weight
        return i1
        
        
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
    
    market1 = Runner(mm_share=mm_share)
    nominals = np.array([market1.insuranceco.portfolio[x]['Nominal'] for x in market1.insuranceco.bond_list])
    xprices = np.array([market1.insuranceco.portfolio[x]['Price']/100 for x in market1.insuranceco.bond_list])
    bond_value = np.sum(nominals*xprices)
    print(100*bond_value/(market1.insuranceco.equity+bond_value))

