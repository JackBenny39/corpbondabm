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
    def __init__(self, name, lower_bound, upper_bound, target):
        '''
        Initialize MutualFund
        
        
        '''
        BuySide.__init__(self, name)
        self.trader_type = 'MutualFund'
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.target = target
        self.nav_history = {}
        self.bond_list = []
        self.portfolio = {}
        self.cash = 0
        self.index_weights = {}
        
    def __repr__(self):
        return 'BuySide({0}, {1})'.format(self._trader_id, self.trader_type)
    
    def compute_weights_from_nominal(self):
        nominals = np.array([self.portfolio[x]['Nominal'] for x in self.bond_list])
        nominal_value = np.sum(nominals)
        weights = nominals/nominal_value
        return dict(zip(self.bond_list, weights))
    
    def compute_portfolio_value(self, prices):
        bond_values = [self.portfolio[x]['Nominal']*prices[x]/100 for x in self.bond_list]
        return np.sum(bond_values)
    
    def add_nav_to_history(self, step, prices):
        nav = self.compute_portfolio_value(prices) + self.cash
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
        rfq =  {'order_id': order_id, 'name': name, 'side': side, 'amount': amount}
        self.rfq_collector.append(rfq)
        
    def modify_portfolio(self, confirm):
        bond = confirm['name']
        if confirm['side'] == 'buy':
            self.portfolio[bond]['Nominal'] += confirm['size']
            self.cash -= confirm['size']*confirm['price']
        else:
            self.portfolio[bond]['Nominal'] -= confirm['size']
            self.cash += confirm['size']*confirm['price']
            
    def make_portfolio_decision(self, step):
        '''
        The MutualFund needs to know:
        1. Cash Position relative to limits
        2. Ranked deviation from Nominal Index Weights (fixed)
        
        And then:
        1. Submits orders if cash is not within the limits
        2. Bond choice reflect deviations from Index
        
        But:
        1. Buying can wait, while
        2. Selling cannot
        '''
        self.rfq_collector.clear()
        actual_weights = self.compute_weights_from_nominal()
        deviations = {k:actual_weights[k]-self.index_weights[k] for k in self.bond_list}
        print(deviations)
        last_nav = self.nav_history[step-1]
        expected_cash_pct = (self.cash + self.compute_flow(step))/last_nav
        if expected_cash_pct < self.lower_bound:
            side = 'sell'
            sell_amount = (self.target - expected_cash_pct)*last_nav
            potential_bonds = sorted(deviations, key=deviations.get)
            for bond in potential_bonds:
                bond_deviation = deviations[bond]*last_nav
                if bond_deviation >= 1:
                    if bond_deviation < sell_amount:
                        self.make_rfq(bond, side, int(bond_deviation))
                        sell_amount -= int(bond_deviation)
                    else:
                        self.make_rfq(bond, side, int(sell_amount))
                    
        elif expected_cash_pct > self.upper_bound:
            side = 'buy'
            buy_amount = (expected_cash_pct - self.target)*last_nav
            potential_bonds = sorted(deviations, key=deviations.get, reverse=True)
            for bond in potential_bonds:
                bond_deviation = -deviations[bond]*last_nav
                if bond_deviation >= 1:
                    if bond_deviation < buy_amount:
                        self.make_rfq(bond, side, int(bond_deviation))
                        buy_amount -= int(bond_deviation)
                    else:
                        self.make_rfq(bond, side, int(buy_amount))
        
    
    
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