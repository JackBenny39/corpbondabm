import time

from corpbondabm.bondmarket2017_r1 import BondMarket
from corpbondabm.trader2017_r1 import MutualFund

class Runner(object):
    
    def __init__(self, market_name='bondmarket1', 
                 mm_name='m1', mm_share=0.15, mm_lower=0.03, mm_upper=0.08, mm_target=0.05):
        self.bondmarket = self.make_market(market_name)
        self.mutualfund = self.make_mutual_fund(mm_name, mm_share, mm_lower, mm_upper, mm_target)
        
    def make_market(self, name):
        bondmarket = BondMarket(name)
        bondmarket.add_bond('MM101', 500, 1, .0175, .015, 2)
        bondmarket.add_bond('MM102', 500, 2, .025, .0175, 2)
        bondmarket.add_bond('MM103', 1000, 5, .0225, .025, 2)
        bondmarket.add_bond('MM104', 2000, 10, .024, .026, 2)
        bondmarket.add_bond('MM105', 1000, 25, .04, .0421, 2)
        return bondmarket
    
    def make_mutual_fund(self, name, share, ll, ul, target):
        m1 = MutualFund(name, ll, ul, target)
        for bond in self.bondmarket.bonds:
            m1.bond_list.append(bond['Name'])
            mm_bond = {'Name': bond['Name'], 'Nominal': share*bond['Nominal'], 'Maturity': bond['Maturity'],
                       'Coupon': bond['Coupon'], 'Yield': bond['Yield'], 'Price': bond['Price']}
            m1.portfolio[bond['Name']] = mm_bond
        prices = {k:m1.portfolio[k]['Price'] for k in m1.bond_list}
        bond_value = m1.compute_portfolio_value(prices)
        m1.cash = target*bond_value/(1-target)
        m1.index_weights = self.bondmarket.compute_weights_from_nominal()
        m1.add_nav_to_history(0, prices)
        return m1
        
        
        
if __name__ == '__main__':
    
    start = time.time()
    print(start)
    #market_name = 'bondmarket1'
    #mutualfund_name = 'm1' 
    mm_share = 0.15
    #mm_lower = 0.03
    #mm_upper = 0.08
    #mm_target = 0.05
    
    market1 = Runner(mm_share=mm_share)
    print(market1.mutualfund.index_weights)
    print(market1.mutualfund.cash)
