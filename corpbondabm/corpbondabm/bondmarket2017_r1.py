import numpy as np

from math import pow


class BondMarket(object):
    '''
    BondMarket
    
    base class for bond market
    '''
    
    def __init__(self, name):
        '''
        Initialize BondMarket with some base class attributes and a method
        
        
        '''
        self._market_id = name # trader id
        self.bonds = []
        
    def __repr__(self):
        return 'BondMarket({0})'.format(self._market_id)
    
    def add_bond(self, name, nominal, maturity, coupon, ytm, nper):
        price = self._price_bond(100, maturity, coupon, ytm, nper)
        self.bonds.append({'Name': name, 'Nominal': nominal, 'Maturity': maturity, 'Coupon': coupon, 'Yield': ytm, 'Price': price})
        
    def _price_bond(self, nominal, maturity, coupon, ytm, nper):
        n = nper*maturity
        payment = nominal*coupon/nper
        rate = ytm/nper
        discount = 1/pow(1+rate,n)
        return payment*(1-discount)/rate + discount*nominal
    
    def compute_weights_from_price(self):
        prices = np.array([x['Price']*x['Nominal']/100 for x in self.bonds])
        market_value = np.sum(prices)
        weights = prices/market_value
        return weights
    
    def compute_weights_from_nominal(self):
        nominals = np.array([x['Nominal'] for x in self.bonds])
        nominal_value = np.sum(nominals)
        weights = nominals/nominal_value
        names = [x['Name'] for x in self.bonds]
        return dict(zip(names, weights))
        
        
        
