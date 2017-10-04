import numpy as np


ALPHA = 0.00017
BETA_D = 0.56
BETA_D1 = -.0002
BETA_W = 0.6
BETA_W1 = -0.0002


class BuySide(object):
    '''
    BuySide
    
    base class for buy side traders
    '''
    
    def __init__(self, name):
        '''
        Initialize BuySide with some base class attributes and a method
        
        rfq is a public container for carrying price quote requests to the sell side
        '''
        self._trader_id = name # trader id
        self.rfq_collector = []
        self._rfq_sequence = 0
        
    def __repr__(self):
        return 'BuySide({0})'.format(self._trader_id)
    
    
class MutualFund(BuySide):
    '''
    MutualFund
        
        
    '''
    def __init__(self, name, lower_bound, upper_bound):
        '''
        Initialize MutualFund
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'MutualFund'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.nav_history = {}
        self.portfolio = []
        self.cash = 0
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def compute_portfolio_value(self):
        bond_values = [x['Nominal'] for x in self.portfolio]
        return np.sum(bond_values)
    
    def add_nav_to_history(self, step):
        nav = self.compute_portfolio_value() + self.cash
        self.nav_history[step] = nav
    
    def compute_flow(self, step):
        wealth_lag1 = self.nav_history[step-1]
        retdaily_lag1 = wealth_lag1/self.nav_history[step-2] - 1
        retweekly_lag1 = wealth_lag1/self.nav_history[step-6] - 1
        flow_ratio = ALPHA + (BETA_D + BETA_D1*(retdaily_lag1<0))*retdaily_lag1 + (BETA_W + BETA_W1*(retweekly_lag1<0))*retweekly_lag1
        return flow_ratio*wealth_lag1
    
    def make_rfq(self, name, side, amount):
        self._rfq_sequence += 1
        order_id = '%s_%d' % (self._trader_id, self._rfq_sequence)
        return {'order_id': order_id, 'name': name, 'side': side, 'amount': amount}
        #self.rfq_collector.append(rfq)
    
    
class InsuranceCo(BuySide):
    '''
    InsuranceCo
        
        
    '''
    def __init__(self, name):
        '''
        Initialize InsuranceCo
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'InsuranceCo'
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    
class HedgeFund(BuySide):
    '''
    HedgeFund
        
        
    '''
    def __init__(self, name):
        '''
        Initialize HedgeFund
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'HedgeFund'
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)